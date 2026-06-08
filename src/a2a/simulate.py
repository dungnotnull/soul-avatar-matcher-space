#!/usr/bin/env python
"""
Simulated A2A match demo: runs N parallel sessions between randomly generated
test avatars with synthetic personality profiles.

Use: python -m src.a2a.simulate [--count 10] [--parallel]
"""

from __future__ import annotations

import sys
import time
import random
import uuid
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from src.avatar.capsule_builder import AvatarCapsuleBuilder
from src.a2a.session_manager import A2ASessionManager
from src.matching.scorer import CompatibilityScorer
from src.consent.gate import ConsentGate
from config.settings import settings


def _random_big_five() -> dict[str, float]:
    return {
        "openness": round(random.uniform(0.1, 0.95), 3),
        "conscientiousness": round(random.uniform(0.1, 0.95), 3),
        "extraversion": round(random.uniform(0.1, 0.95), 3),
        "agreeableness": round(random.uniform(0.1, 0.95), 3),
        "neuroticism": round(random.uniform(0.1, 0.95), 3),
    }


def _random_emotions() -> dict[str, float]:
    raw = {
        "joy": random.uniform(0, 1),
        "sadness": random.uniform(0, 1),
        "anger": random.uniform(0, 1),
        "fear": random.uniform(0, 1),
        "surprise": random.uniform(0, 1),
        "disgust": random.uniform(0, 1),
        "neutral": random.uniform(0, 1),
    }
    total = sum(raw.values())
    return {k: round(v / total, 4) for k, v in raw.items()}


def _random_vector(dim: int = 512) -> np.ndarray:
    vec = np.random.randn(dim).astype(np.float64)
    return vec / (np.linalg.norm(vec) + 1e-8)


def create_test_avatar(avatar_id: str | None = None) -> tuple[AvatarCapsuleBuilder, object]:
    aid = avatar_id or str(uuid.uuid4())[:8]
    builder = AvatarCapsuleBuilder(avatar_id=aid)
    capsule = builder.build(
        vector=_random_vector(),
        big_five=_random_big_five(),
        emotions=_random_emotions(),
        source_texts=[f"Sample text for avatar {aid}"],
    )
    return builder, capsule


def run_single_match(pair_id: int, quiet: bool = False) -> dict:
    _, capsule_a = create_test_avatar()
    _, capsule_b = create_test_avatar()

    manager = A2ASessionManager()
    session = manager.create_session(capsule_a, capsule_b)

    try:
        transcript = manager.run_debate(session)
    except Exception as e:
        if not quiet:
            logger.warning(f"[Match {pair_id}] SLM debate failed: {e}")
        transcript = []

    scorer = CompatibilityScorer()
    score, breakdown = scorer.compute(capsule_a, capsule_b, transcript)
    matched = score >= settings.COMPATIBILITY_THRESHOLD

    consent_result = None
    if matched:
        gate = ConsentGate()
        match_id = gate.initiate_match(capsule_a, capsule_b, score)
        result_a = gate.process_decision(match_id, capsule_a.avatar_id, True)
        result_b = gate.process_decision(match_id, capsule_b.avatar_id, True)
        consent_result = result_b

    if not quiet:
        status = "✓ MATCH" if matched else "✗ no match"
        logger.info(
            f"[Match {pair_id}] {status} | composite={score:.4f} | "
            f"vec={breakdown['vector_similarity']:.4f} | "
            f"dialogue={breakdown['dialogue_coherence']:.4f} | "
            f"bonus={breakdown['complementarity_bonus']:.4f}"
        )

    return {
        "pair_id": pair_id,
        "avatar_a": capsule_a.avatar_id,
        "avatar_b": capsule_b.avatar_id,
        "score": round(score, 4),
        "breakdown": breakdown,
        "matched": matched,
        "transcript_length": len(transcript),
    }


def run_simulation(count: int = 10, parallel: bool = False, max_workers: int = 10):
    logger.info(f"Starting {count} simulated A2A match sessions (parallel={parallel})...")
    start = time.time()
    results = []

    if parallel:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(run_single_match, i, False): i for i in range(count)}
            for future in as_completed(futures):
                results.append(future.result())
    else:
        for i in range(count):
            results.append(run_single_match(i, False))

    elapsed = time.time() - start
    matched_count = sum(1 for r in results if r["matched"])
    scores = [r["score"] for r in results]

    print()
    print("=" * 60)
    print(f"  SIMULATION COMPLETE: {count} sessions in {elapsed:.2f}s")
    print(f"  Matches above threshold: {matched_count}/{count}")
    print(f"  Score range: [{min(scores):.4f} - {max(scores):.4f}]")
    print(f"  Mean score: {np.mean(scores):.4f}")
    print(f"  Median score: {np.median(scores):.4f}")
    print(f"  Match rate: {matched_count/count*100:.1f}%")
    print("=" * 60)

    return results


def main():
    count = 10
    parallel = False
    workers = 10

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ("--count", "-c") and i + 1 < len(args):
            count = int(args[i + 1])
        if arg in ("--parallel", "-p"):
            parallel = True
        if arg in ("--workers", "-w") and i + 1 < len(args):
            workers = int(args[i + 1])

    run_simulation(count=count, parallel=parallel, max_workers=workers)


if __name__ == "__main__":
    main()
