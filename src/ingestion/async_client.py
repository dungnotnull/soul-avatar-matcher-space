"""
Async data ingestion client with retry, exponential backoff, and circuit breaker.

Handles folder 3 (knowledge graph) and folder 5 (presence) API connections
with robust error handling and graceful degradation.
"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import httpx
from loguru import logger

from config.settings import settings


@dataclass
class IngestionBatch:
    user_id: str
    texts: list[str]
    source: str
    fetched_at: datetime = field(default_factory=datetime.now)
    fingerprint: str = ""


class AsyncDataIngestionClient:
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        circuit_breaker_threshold: int = 5,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self._failures: dict[str, int] = {}
        self._last_failure: dict[str, datetime] = {}
        self._circuit_open_until: dict[str, datetime] = {}
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _is_circuit_open(self, source: str) -> bool:
        if source in self._circuit_open_until:
            if datetime.now() < self._circuit_open_until[source]:
                return True
            del self._circuit_open_until[source]
            self._failures[source] = 0
        return False

    def _record_failure(self, source: str):
        self._failures[source] = self._failures.get(source, 0) + 1
        self._last_failure[source] = datetime.now()
        if self._failures[source] >= self.circuit_breaker_threshold:
            backoff = min(300, self.backoff_base * (2 ** self._failures[source]))
            self._circuit_open_until[source] = datetime.now() + timedelta(seconds=backoff)
            logger.warning(f"Circuit breaker OPEN for {source} until {self._circuit_open_until[source]}")

    def _record_success(self, source: str):
        self._failures[source] = max(0, self._failures.get(source, 0) - 2)

    async def _fetch_with_retry(self, url: str, params: dict | None = None, source: str = "") -> httpx.Response:
        if self._is_circuit_open(source):
            raise httpx.ConnectError(f"Circuit breaker open for {source}")

        client = await self._get_client()
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                self._record_success(source)
                return resp
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    wait = self.backoff_base * (2 ** attempt)
                    logger.debug(f"Retry {attempt+1}/{self.max_retries} for {source}: waiting {wait:.1f}s")
                    await asyncio.sleep(wait)
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    last_exc = e
                    if attempt < self.max_retries - 1:
                        wait = self.backoff_base * (2 ** attempt)
                        await asyncio.sleep(wait)
                        continue
                raise

        self._record_failure(source)
        raise last_exc or httpx.ConnectError(f"All {self.max_retries} retries exhausted for {source}")

    async def fetch_folder3(self, user_id: str, limit: int = 50) -> IngestionBatch:
        url = f"{settings.FOLDER3_API_URL}/api/knowledge/{user_id}/texts"
        source = "folder3"
        try:
            resp = await self._fetch_with_retry(
                url, params={"limit": limit}, source=source
            )
            data = resp.json()
            texts = data.get("texts", []) if isinstance(data, dict) else data
            logger.info(f"Async fetch folder3: {len(texts)} texts for {user_id}")
            return IngestionBatch(
                user_id=user_id,
                texts=texts,
                source=source,
                fingerprint=hashlib.sha256(str(texts).encode()).hexdigest()[:16],
            )
        except Exception:
            logger.info(f"Folder 3 unreachable, returning empty batch for {user_id}")
            return IngestionBatch(user_id=user_id, texts=[], source=source)

    async def fetch_folder5(self, user_id: str, limit: int = 50) -> IngestionBatch:
        url = f"{settings.FOLDER5_API_URL}/api/presence/{user_id}/texts"
        source = "folder5"
        try:
            resp = await self._fetch_with_retry(
                url, params={"limit": limit}, source=source
            )
            data = resp.json()
            texts = data.get("texts", []) if isinstance(data, dict) else data
            logger.info(f"Async fetch folder5: {len(texts)} texts for {user_id}")
            return IngestionBatch(
                user_id=user_id,
                texts=texts,
                source=source,
                fingerprint=hashlib.sha256(str(texts).encode()).hexdigest()[:16],
            )
        except Exception:
            logger.info(f"Folder 5 unreachable, returning empty batch for {user_id}")
            return IngestionBatch(user_id=user_id, texts=[], source=source)

    async def fetch_all(self, user_id: str, limit: int = 50) -> IngestionBatch:
        batch3, batch5 = await asyncio.gather(
            self.fetch_folder3(user_id, limit),
            self.fetch_folder5(user_id, limit),
        )
        combined = list(dict.fromkeys(batch3.texts + batch5.texts))
        return IngestionBatch(
            user_id=user_id,
            texts=combined,
            source="folder3+folder5",
            fingerprint=hashlib.sha256(str(combined).encode()).hexdigest()[:16],
        )

    async def fetch_batch_users(
        self,
        user_ids: list[str],
        limit: int = 50,
        max_concurrency: int = 10,
    ) -> dict[str, IngestionBatch]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _fetch_one(uid: str) -> tuple[str, IngestionBatch]:
            async with semaphore:
                return uid, await self.fetch_all(uid, limit)

        tasks = [_fetch_one(uid) for uid in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output: dict[str, IngestionBatch] = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch fetch error: {result}")
                continue
            uid, batch = result
            output[uid] = batch
        return output

    @staticmethod
    async def from_files(paths: list[str]) -> IngestionBatch:
        texts = []
        for path in paths:
            p = Path(path)
            if p.exists():
                content = p.read_text(encoding="utf-8")
                texts.extend(line.strip() for line in content.split("\n") if line.strip())
        return IngestionBatch(
            user_id="file-import",
            texts=texts,
            source="files",
            fingerprint=hashlib.sha256("".join(texts).encode()).hexdigest()[:16],
        )
