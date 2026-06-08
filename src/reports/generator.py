"""
Enhanced report generator with prompt caching, exponential retry/backoff,
and robust config validation for all LLM backends.
"""

from __future__ import annotations

import time
import hashlib
from dataclasses import dataclass, field
from loguru import logger

from proto.avatar_pb2 import AvatarCapsule
from src.avatar.capsule_builder import AvatarCapsuleBuilder
from src.a2a.slm_reasoner import LocalSLMReasoner
from config.settings import settings
from config.llm_settings import LLMProvider, resolve_provider, resolve_with_fallback
from src.reports import prompts


@dataclass
class PromptCacheEntry:
    prompt_hash: str
    response: str
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 3600


class ReportGenerator:
    def __init__(self, cache_size: int = 100, cache_ttl: int = 3600):
        self.builder = AvatarCapsuleBuilder()
        self._ollama_reasoner: LocalSLMReasoner | None = None
        self._cache: dict[str, PromptCacheEntry] = {}
        self._cache_size = cache_size
        self._cache_ttl = cache_ttl
        self._max_retries = 3
        self._backoff_base = 1.5

    @property
    def ollama(self) -> LocalSLMReasoner:
        if self._ollama_reasoner is None:
            self._ollama_reasoner = LocalSLMReasoner()
        return self._ollama_reasoner

    def generate(
        self,
        self_capsule: AvatarCapsule,
        other_capsule: AvatarCapsule,
        compatibility_score: float,
        recipient_id: str,
        preferred_provider: LLMProvider | None = None,
    ) -> str:
        provider = resolve_with_fallback(preferred_provider)
        logger.info(f"Generating report via {provider.value} for recipient {recipient_id}")

        bf_a = self.builder.capsule_to_big_five(self_capsule)
        bf_b = self.builder.capsule_to_big_five(other_capsule)
        em_a = self.builder.capsule_to_emotions(self_capsule)
        em_b = self.builder.capsule_to_emotions(other_capsule)

        similar, different = self._trait_comparison(bf_a, bf_b)
        comm_alignment = self._communication_alignment(bf_a, bf_b)

        prompt = prompts.COMPATIBILITY_REPORT_PROMPT.format(
            oa=bf_a["openness"], ca=bf_a["conscientiousness"],
            ea=bf_a["extraversion"], aa=bf_a["agreeableness"],
            na=bf_a["neuroticism"],
            em_a=max(em_a, key=em_a.get),
            ob=bf_b["openness"], cb=bf_b["conscientiousness"],
            eb=bf_b["extraversion"], ab=bf_b["agreeableness"],
            nb=bf_b["neuroticism"],
            em_b=max(em_b, key=em_b.get),
            score=compatibility_score,
            similar_traits=", ".join(similar) if similar else "none strongly",
            different_traits=", ".join(different) if different else "none strongly",
            comm_alignment=comm_alignment,
        )

        cached = self._check_cache(prompt)
        if cached is not None:
            logger.debug("Using cached report response.")
            return cached

        try:
            response = self._generate_with_retry(prompt, provider)
            self._update_cache(prompt, response)
            return response
        except Exception as e:
            logger.error(f"Report generation via {provider.value} exhausted retries: {e}")
            if provider != LLMProvider.OLLAMA:
                logger.info("Falling back to Ollama for report generation.")
                return self._generate_ollama_with_retry(prompt)
            return self._fallback_report(compatibility_score, similar, different)

    def _generate_with_retry(self, prompt: str, provider: LLMProvider) -> str:
        last_exc = None
        for attempt in range(self._max_retries):
            try:
                if provider == LLMProvider.CLAUDE:
                    return self._generate_claude_cached(prompt)
                elif provider == LLMProvider.OPENAI:
                    return self._generate_openai(prompt)
                else:
                    return self._generate_ollama_with_retry(prompt)
            except Exception as e:
                last_exc = e
                if attempt < self._max_retries - 1:
                    wait = self._backoff_base ** attempt
                    logger.warning(f"LLM retry {attempt+1}/{self._max_retries}: waiting {wait:.1f}s (error: {e})")
                    time.sleep(wait)
        raise last_exc or RuntimeError("All retries exhausted without specific error")

    def _generate_ollama_with_retry(self, prompt: str) -> str:
        last_exc = None
        for attempt in range(self._max_retries):
            try:
                return self.ollama.generate(
                    prompt=prompt,
                    system=prompts.OLLAMA_SYSTEM_PROMPT,
                    temperature=0.6,
                    max_tokens=400,
                )
            except Exception as e:
                last_exc = e
                if attempt < self._max_retries - 1:
                    wait = self._backoff_base ** attempt
                    time.sleep(wait)
        raise last_exc or RuntimeError("Ollama retries exhausted")

    def _generate_claude_cached(self, prompt: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        resp = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=600,
            system=[
                {
                    "type": "text",
                    "text": prompts.CLAUDE_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()

    def _generate_openai(self, prompt: str) -> str:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=600,
            messages=[
                {"role": "system", "content": prompts.OPENAI_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content.strip()

    def _check_cache(self, prompt: str) -> str | None:
        key = hashlib.md5(prompt.encode()).hexdigest()
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.time() - entry.created_at > entry.ttl_seconds:
            del self._cache[key]
            return None
        return entry.response

    def _update_cache(self, prompt: str, response: str):
        if len(self._cache) >= self._cache_size:
            oldest = min(self._cache.values(), key=lambda e: e.created_at)
            oldest_key = next(k for k, v in self._cache.items() if v is oldest)
            del self._cache[oldest_key]
        key = hashlib.md5(prompt.encode()).hexdigest()
        self._cache[key] = PromptCacheEntry(key, response, ttl_seconds=self._cache_ttl)

    def _fallback_report(self, score: float, similar: list[str], different: list[str]) -> str:
        return (
            f"Compatibility Summary\n\n"
            f"This match shows a {score:.0%} compatibility based on personality alignment.\n\n"
            f"Strengths: Strong alignment in {', '.join(similar) if similar else 'core values'}.\n"
            f"Growth areas: Different perspectives on {', '.join(different) if different else 'communication style'} may require mutual understanding.\n\n"
            f"Overall, this connection has meaningful potential if both individuals approach differences with curiosity and openness."
        )

    def _trait_comparison(self, bf_a: dict[str, float], bf_b: dict[str, float]) -> tuple[list[str], list[str]]:
        similar = []
        different = []
        trait_labels = {
            "openness": "openness to experience",
            "conscientiousness": "conscientiousness",
            "extraversion": "extraversion",
            "agreeableness": "agreeableness",
            "neuroticism": "emotional stability",
        }
        for key, label in trait_labels.items():
            diff = abs(bf_a[key] - bf_b[key])
            if diff < 0.15:
                similar.append(label)
            elif diff > 0.3:
                different.append(label)
        return similar, different

    def _communication_alignment(self, bf_a: dict[str, float], bf_b: dict[str, float]) -> str:
        e_diff = abs(bf_a["extraversion"] - bf_b["extraversion"])
        a_avg = (bf_a["agreeableness"] + bf_b["agreeableness"]) / 2
        if e_diff < 0.2 and a_avg > 0.6:
            return "naturally harmonious"
        elif e_diff > 0.4 and a_avg > 0.5:
            return "complementary but may require adjustment"
        elif e_diff < 0.2 and a_avg < 0.4:
            return "direct and potentially challenging"
        else:
            return "moderately aligned"


def validate_config() -> dict[str, bool | str]:
    results = {}
    if settings.CLAUDE_API_KEY:
        try:
            import anthropic
            anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
            results["claude"] = True
        except Exception as e:
            results["claude"] = str(e)
    else:
        results["claude"] = "no API key configured"
    if settings.OPENAI_API_KEY:
        try:
            import openai
            openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            results["openai"] = True
        except Exception as e:
            results["openai"] = str(e)
    else:
        results["openai"] = "no API key configured"
    reasoner = LocalSLMReasoner()
    results["ollama"] = reasoner.health_check()
    return results
