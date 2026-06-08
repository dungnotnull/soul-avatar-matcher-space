"""
Compatibility scorer — hybrid scoring combining cosine similarity on personality vectors
and LLM-judged dialogue coherence from A2A debate transcripts.

Produces weighted composite score with complementarity bonuses.
"""

from __future__ import annotations

import numpy as np
from loguru import logger

from proto.avatar_pb2 import AvatarCapsule
from src.avatar.capsule_builder import AvatarCapsuleBuilder
from config.settings import settings


class CompatibilityScorer:
    """
    Computes compatibility between two avatar capsules using:
    1. Cosine similarity on 512-dim personality vectors (primary signal)
    2. LLM judge evaluating debate transcript coherence (secondary signal)
    3. Complementarity bonus for E/I pairings and high-O/low-C pairings
    """

    def __init__(self, reasoner=None):
        self._reasoner = reasoner
        self.builder = AvatarCapsuleBuilder()

    def compute(
        self,
        capsule_a: AvatarCapsule,
        capsule_b: AvatarCapsule,
        transcript: list[dict] | None = None,
    ) -> tuple[float, dict]:
        """
        Compute weighted composite compatibility score.
        Returns (score, breakdown_dict).
        """
        vec_score = self._vector_similarity(capsule_a, capsule_b)
        complementarity_bonus = self._complementarity_bonus(capsule_a, capsule_b)

        dialogue_score = 0.5
        if transcript:
            dialogue_score = self._judge_dialogue(capsule_a, capsule_b, transcript)

        vector_weight = settings.VECTOR_WEIGHT
        dialogue_weight = settings.DIALOGUE_WEIGHT

        composite = (vector_weight * vec_score) + (dialogue_weight * dialogue_score) + complementarity_bonus
        composite = max(0.0, min(1.0, composite))

        breakdown = {
            "vector_similarity": round(vec_score, 4),
            "dialogue_coherence": round(dialogue_score, 4),
            "complementarity_bonus": round(complementarity_bonus, 4),
            "composite_score": round(composite, 4),
            "weights": {"vector": vector_weight, "dialogue": dialogue_weight},
        }

        logger.info(f"Compatibility scored: composite={composite:.4f} (vec={vec_score:.4f}, dialogue={dialogue_score:.4f}, bonus={complementarity_bonus:.4f})")
        return composite, breakdown

    def _vector_similarity(self, capsule_a: AvatarCapsule, capsule_b: AvatarCapsule) -> float:
        vec_a = self.builder.capsule_to_vector(capsule_a)
        vec_b = self.builder.capsule_to_vector(capsule_b)
        similarity = float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b) + 1e-8))
        return similarity

    def _complementarity_bonus(self, capsule_a: AvatarCapsule, capsule_b: AvatarCapsule) -> float:
        """
        Complementarity bonus for known beneficial pairings:
        - Extraversion/Introversion complement: up to +0.08
        - High Openness / Low Conscientiousness: up to +0.04
        """
        bonus = 0.0
        bf_a = self.builder.capsule_to_big_five(capsule_a)
        bf_b = self.builder.capsule_to_big_five(capsule_b)

        e_diff = abs(bf_a["extraversion"] - bf_b["extraversion"])
        if e_diff > 0.4:
            bonus += 0.08 * min(e_diff, 0.8)

        o_a = bf_a["openness"]
        o_b = bf_b["openness"]
        c_a = bf_a["conscientiousness"]
        c_b = bf_b["conscientiousness"]

        if (o_a > 0.7 and c_b < 0.4) or (o_b > 0.7 and c_a < 0.4):
            bonus += 0.04

        return bonus

    def _judge_dialogue(
        self,
        capsule_a: AvatarCapsule,
        capsule_b: AvatarCapsule,
        transcript: list[dict],
    ) -> float:
        """
        LLM judge evaluates dialogue coherence and value alignment.
        Falls back to heuristic if reasoner unavailable.
        """
        if self._reasoner is None:
            return self._heuristic_dialogue_score(transcript)

        dialogue_text = "\n".join(
            f"{t['speaker_id']}: {t['content']}" for t in transcript[-10:]
        )

        judge_prompt = (
            f"You are evaluating compatibility between two people based on their debate transcript.\n\n"
            f"Avatar A traits: Openness={capsule_a.big_five.openness:.2f}, "
            f"Conscientiousness={capsule_a.big_five.conscientiousness:.2f}, "
            f"Extraversion={capsule_a.big_five.extraversion:.2f}, "
            f"Agreeableness={capsule_a.big_five.agreeableness:.2f}, "
            f"Neuroticism={capsule_a.big_five.neuroticism:.2f}\n\n"
            f"Avatar B traits: Openness={capsule_b.big_five.openness:.2f}, "
            f"Conscientiousness={capsule_b.big_five.conscientiousness:.2f}, "
            f"Extraversion={capsule_b.big_five.extraversion:.2f}, "
            f"Agreeableness={capsule_b.big_five.agreeableness:.2f}, "
            f"Neuroticism={capsule_b.big_five.neuroticism:.2f}\n\n"
            f"Dialogue:\n{dialogue_text}\n\n"
            f"On a scale of 0.0 to 1.0, how compatible are these two people based on this dialogue? "
            f"Consider: coherence, mutual understanding, value alignment, communication chemistry. "
            f"Reply with only a single float number."
        )

        try:
            raw = self._reasoner.generate(judge_prompt, system="You are a compatibility judge.", temperature=0.3)
            score = float(raw.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"LLM judge failed: {e}. Using heuristic score.")
            return self._heuristic_dialogue_score(transcript)

    def _heuristic_dialogue_score(self, transcript: list[dict]) -> float:
        """Simple heuristic based on response length and turn count."""
        if not transcript:
            return 0.5
        avg_len = np.mean([len(t["content"].split()) for t in transcript])
        coherence = min(1.0, avg_len / 40.0)
        engagement = min(1.0, len(transcript) / 20.0)
        return 0.5 * coherence + 0.5 * engagement

    def batch_score(
        self,
        pairs: list[tuple[AvatarCapsule, AvatarCapsule]],
    ) -> list[tuple[float, dict]]:
        """Score multiple capsule pairs efficiently."""
        return [self.compute(a, b) for a, b in pairs]
