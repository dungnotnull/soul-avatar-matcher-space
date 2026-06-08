"""
Data ingestion client for folder 3 (omni-second-brain-agent) and folder 5 (omni-presence-soulmate).

Fetches behavioral text data via REST API with fallback to manual text input.
"""

from __future__ import annotations

import httpx
from loguru import logger

from config.settings import settings


class DataIngestionClient:
    def __init__(self, timeout: int | None = None):
        self.timeout = timeout or settings.INGESTION_TIMEOUT
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def fetch_folder3_texts(self, user_id: str, limit: int = 50) -> list[str]:
        """
        Pull behavioral text data from folder 3 (knowledge graph agent).
        Expected endpoint: GET /api/knowledge/{user_id}/texts?limit={limit}
        """
        url = f"{settings.FOLDER3_API_URL}/api/knowledge/{user_id}/texts"
        try:
            resp = self.client.get(url, params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
            texts = data.get("texts", []) if isinstance(data, dict) else data
            logger.info(f"Fetched {len(texts)} texts from folder 3 for user {user_id}")
            return texts
        except httpx.ConnectError:
            logger.warning(f"Folder 3 API unreachable at {settings.FOLDER3_API_URL}")
            return []
        except Exception as e:
            logger.error(f"Folder 3 fetch failed: {e}")
            return []

    def fetch_folder5_texts(self, user_id: str, limit: int = 50) -> list[str]:
        """
        Pull behavioral text data from folder 5 (presence agent).
        Expected endpoint: GET /api/presence/{user_id}/texts?limit={limit}
        """
        url = f"{settings.FOLDER5_API_URL}/api/presence/{user_id}/texts"
        try:
            resp = self.client.get(url, params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
            texts = data.get("texts", []) if isinstance(data, dict) else data
            logger.info(f"Fetched {len(texts)} texts from folder 5 for user {user_id}")
            return texts
        except httpx.ConnectError:
            logger.warning(f"Folder 5 API unreachable at {settings.FOLDER5_API_URL}")
            return []
        except Exception as e:
            logger.error(f"Folder 5 fetch failed: {e}")
            return []

    def fetch_all(self, user_id: str, limit: int = 50) -> list[str]:
        """Fetch texts from both folder 3 and folder 5, deduplicated."""
        f3 = self.fetch_folder3_texts(user_id, limit)
        f5 = self.fetch_folder5_texts(user_id, limit)
        combined = list(dict.fromkeys(f3 + f5))
        if not combined:
            logger.warning(f"No data fetched from folder 3 or 5 for user {user_id}")
        return combined

    @staticmethod
    def manual_input() -> list[str]:
        """Fallback: accept manual text input from CLI."""
        print("Enter behavioral text samples (one per line, blank line to finish):")
        texts = []
        while True:
            line = input()
            if not line.strip():
                break
            texts.append(line.strip())
        return texts

    @staticmethod
    def from_file(path: str) -> list[str]:
        """Read texts from a file, one sample per line."""
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
