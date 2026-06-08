"""
Dynamic debate topic selector based on personality profiles.

Given two personality profiles, selects the most informative debate topics
that maximize differentiation between compatible and incompatible pairings.
"""

from __future__ import annotations

import numpy as np
from proto.avatar_pb2 import AvatarCapsule
from src.avatar.capsule_builder import AvatarCapsuleBuilder
from src.a2a.debate_topics import DEBATE_TOPICS, get_all_topic_ids


class DynamicTopicSelector:
    """
    Selects debate topics personalized to the two avatars' personality profiles.
    
    Strategy:
    - Topics where Big Five differences are largest → highest informational value
    - Also includes mandatory baseline topics (values, communication) for minimum coverage
    - Ensures topic diversity across all Big Five dimensions
    """

    MANDATORY_TOPICS = {"values", "communication"}
    MAX_TOPICS = 5

    def __init__(self):
        self.builder = AvatarCapsuleBuilder()

    def select(
        self,
        capsule_a: AvatarCapsule,
        capsule_b: AvatarCapsule,
        num_topics: int = 5,
    ) -> list[str]:
        bf_a = self.builder.capsule_to_big_five(capsule_a)
        bf_b = self.builder.capsule_to_big_five(capsule_b)
        diffs = {
            t: abs(bf_a[t] - bf_b[t])
            for t in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        }

        topic_mapping = self._build_trait_mapping()
        scored = []
        for topic_id in get_all_topic_ids():
            if topic_id in self.MANDATORY_TOPICS:
                scored.append((topic_id, 2.0))
                continue
            trait = topic_mapping.get(topic_id, "openness")
            score = diffs.get(trait, 0.5)
            scored.append((topic_id, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        selected = []
        mandatory_seen = set()
        for topic_id, _ in scored:
            if topic_id in self.MANDATORY_TOPICS:
                if topic_id not in mandatory_seen:
                    selected.append(topic_id)
                    mandatory_seen.add(topic_id)
            elif len(selected) < num_topics:
                if topic_id not in mandatory_seen:
                    selected.append(topic_id)

        while len(selected) < min(num_topics, len(scored)):
            for topic_id, _ in scored:
                if topic_id not in selected:
                    selected.append(topic_id)
                    break

        return selected[:num_topics]

    def _build_trait_mapping(self) -> dict[str, str]:
        return {
            "finance": "conscientiousness",
            "conflict": "agreeableness",
            "creativity": "openness",
            "lifestyle": "conscientiousness",
            "values": "agreeableness",
            "risk": "neuroticism",
            "communication": "extraversion",
            "family": "agreeableness",
            "ambition": "extraversion",
            "humor": "openness",
        }

    def select_with_explanation(
        self,
        capsule_a: AvatarCapsule,
        capsule_b: AvatarCapsule,
    ) -> list[dict]:
        selected_ids = self.select(capsule_a, capsule_b)
        all_topics = {t["id"]: t for t in DEBATE_TOPICS}
        result = []
        for tid in selected_ids:
            topic = all_topics.get(tid, {"id": tid, "title": tid})
            result.append(topic)
        return result
