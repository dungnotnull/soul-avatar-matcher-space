"""
Avatar capsule builder — packages personality vector, Big Five scores, emotion distribution,
and behavioral fingerprint into a protobuf capsule for A2A transport.
"""

from __future__ import annotations

import hashlib
import time
import uuid
import numpy as np

from proto import avatar_pb2
from config.settings import settings


class AvatarCapsuleBuilder:
    def __init__(self, avatar_id: str | None = None, slm_endpoint: str | None = None):
        self.avatar_id = avatar_id or str(uuid.uuid4())
        self.slm_endpoint = slm_endpoint or f"{settings.OLLAMA_BASE_URL}/api/generate"

    def build(
        self,
        vector: np.ndarray,
        big_five: dict[str, float],
        emotions: dict[str, float],
        source_texts: list[str] | None = None,
        drift_delta: float = 0.0,
    ) -> avatar_pb2.AvatarCapsule:
        capsule = avatar_pb2.AvatarCapsule()
        capsule.avatar_id = self.avatar_id
        capsule.slm_endpoint = self.slm_endpoint
        capsule.created_at = int(time.time())
        capsule.drift_delta = drift_delta

        # Vector
        capsule.vector.values.extend(vector.astype(np.float64).tolist())

        # Big Five
        capsule.big_five.openness = big_five.get("openness", 0)
        capsule.big_five.conscientiousness = big_five.get("conscientiousness", 0)
        capsule.big_five.extraversion = big_five.get("extraversion", 0)
        capsule.big_five.agreeableness = big_five.get("agreeableness", 0)
        capsule.big_five.neuroticism = big_five.get("neuroticism", 0)

        # Emotions
        capsule.avg_emotion.joy = emotions.get("joy", 0)
        capsule.avg_emotion.sadness = emotions.get("sadness", 0)
        capsule.avg_emotion.anger = emotions.get("anger", 0)
        capsule.avg_emotion.fear = emotions.get("fear", 0)
        capsule.avg_emotion.surprise = emotions.get("surprise", 0)
        capsule.avg_emotion.disgust = emotions.get("disgust", 0)
        capsule.avg_emotion.neutral = emotions.get("neutral", 0)

        # Fingerprint
        if source_texts:
            combined = "|".join(source_texts).encode("utf-8")
            capsule.fingerprint.hash = hashlib.sha256(combined).digest()
            capsule.fingerprint.window_count = len(source_texts)
        capsule.fingerprint.last_updated = int(time.time())

        return capsule

    def capsule_to_vector(self, capsule: avatar_pb2.AvatarCapsule) -> np.ndarray:
        return np.array(list(capsule.vector.values), dtype=np.float64)

    def capsule_to_big_five(self, capsule: avatar_pb2.AvatarCapsule) -> dict[str, float]:
        return {
            "openness": capsule.big_five.openness,
            "conscientiousness": capsule.big_five.conscientiousness,
            "extraversion": capsule.big_five.extraversion,
            "agreeableness": capsule.big_five.agreeableness,
            "neuroticism": capsule.big_five.neuroticism,
        }

    def capsule_to_emotions(self, capsule: avatar_pb2.AvatarCapsule) -> dict[str, float]:
        return {
            "joy": capsule.avg_emotion.joy,
            "sadness": capsule.avg_emotion.sadness,
            "anger": capsule.avg_emotion.anger,
            "fear": capsule.avg_emotion.fear,
            "surprise": capsule.avg_emotion.surprise,
            "disgust": capsule.avg_emotion.disgust,
            "neutral": capsule.avg_emotion.neutral,
        }
