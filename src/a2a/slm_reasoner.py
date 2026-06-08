"""
Local SLM Reasoner — wraps Ollama API to generate avatar responses during A2A debates.

Runs entirely on-device. No conversation data leaves the machine.
Supports both synchronous generation and real-time streaming via Ollama's SSE endpoint.
"""

from __future__ import annotations

import json
import httpx
from loguru import logger

from config.settings import settings


class LocalSLMReasoner:
    """
    Generates avatar dialogue during A2A sessions using Ollama-hosted SLM.
    Supports streaming generation for real-time debate turn delivery.
    """

    SYSTEM_PROMPT = (
        "You are an AI avatar representing a real person's personality, values, "
        "and communication style. You are participating in a compatibility debate "
        "with another person's avatar. Stay true to your assigned personality profile. "
        "Respond naturally as if you were that person, not an AI assistant. "
        "Be concise — 2-4 sentences per response. Do not break character."
    )

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 200,
    ) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or self.SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            resp = httpx.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except httpx.ConnectError:
            logger.warning(f"Ollama unreachable at {self.base_url}")
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"SLM generation failed: {e}")
            return self._fallback_response(prompt)

    async def generate_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 200,
    ):
        """Stream tokens from Ollama's /api/generate endpoint with stream=True.

        Yields incremental token strings as they arrive. The last yielded value
        is the complete accumulated response string, which the caller can use
        to distinguish streaming-complete.
        """
        import asyncio
        import httpx

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or self.SYSTEM_PROMPT,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
                full_response = ""
                async with client.stream("POST", url, json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            full_response += token
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                yield full_response.strip()
        except httpx.ConnectError:
            logger.warning(f"Ollama streaming unreachable at {self.base_url}")
            fallback = self._fallback_response(prompt)
            yield fallback
        except Exception as e:
            logger.error(f"SLM streaming generation failed: {e}")
            yield self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Generate a simple fallback response when Ollama is unavailable."""
        return (
            "I appreciate the perspective you're sharing. "
            "Let me reflect on that and consider how it aligns with my own views."
        )

    def debate_response(
        self,
        topic: str,
        personality_context: str,
        previous_turns: list[str] | None = None,
    ) -> str:
        """Generate a debate response with personality context and debate history."""
        history = ""
        if previous_turns:
            history = "Previous exchange:\n" + "\n".join(previous_turns[-4:]) + "\n\n"

        prompt = (
            f"{history}"
            f"Topic: {topic}\n"
            f"Your personality profile: {personality_context}\n\n"
            f"As this person, share your genuine thoughts on this topic. "
            f"Respond naturally in first-person."
        )
        return self.generate(prompt)

    async def debate_response_stream(
        self,
        topic: str,
        personality_context: str,
        previous_turns: list[str] | None = None,
    ):
        """Stream a debate response token by token, yielding only incremental content.

        Yields each token as it arrives from the SLM. The final yielded value
        is the complete accumulated response so the caller can record the transcript.
        """
        history = ""
        if previous_turns:
            history = "Previous exchange:\n" + "\n".join(previous_turns[-4:]) + "\n\n"

        prompt = (
            f"{history}"
            f"Topic: {topic}\n"
            f"Your personality profile: {personality_context}\n\n"
            f"As this person, share your genuine thoughts on this topic. "
            f"Respond naturally in first-person."
        )
        accumulated = ""
        last_chunk = None
        async for chunk in self.generate_stream(prompt):
            accumulated += chunk
            last_chunk = chunk
            yield chunk
        if last_chunk != accumulated.strip():
            yield accumulated.strip()

    def health_check(self) -> bool:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
