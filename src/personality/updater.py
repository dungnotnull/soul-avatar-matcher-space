"""
Nightly personality update loop.

Pulls new behavioral text → re-runs extractors → updates vector in vault → logs drift.
Runs on a configurable schedule via a simple scheduler or triggered manually.
"""

from __future__ import annotations

import time
import hashlib
from datetime import datetime
from loguru import logger

from config.settings import settings
from src.personality.extractor import PersonalityExtractor
from src.personality.siamese_model import SiamesePersonalityModel
from src.vault.manager import PersonalityVaultManager


class PersonalityUpdater:
    def __init__(
        self,
        extractor: PersonalityExtractor | None = None,
        encoder: SiamesePersonalityModel | None = None,
        vault: PersonalityVaultManager | None = None,
    ):
        self.extractor = extractor or PersonalityExtractor()
        self.encoder = encoder or SiamesePersonalityModel()
        self.vault = vault or PersonalityVaultManager()

    def update(
        self,
        user_id: str,
        texts: list[str],
        force: bool = False,
    ) -> dict:
        """
        Process new text windows, update personality vector, and return update summary.
        """
        logger.info(f"Updating personality for user {user_id} with {len(texts)} text windows...")

        # Extract traits from new texts
        bf_list, em_list = self.extractor.extract_batch(texts)
        avg_bf, avg_em = PersonalityExtractor.aggregate_profiles(bf_list, em_list)

        # Encode to personality vector
        combined = " ".join(texts)
        vector = self.encoder.encode_single(combined)

        # Compute fingerprint
        fp_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

        # Store in vault
        row_id = self.vault.store_vector(
            user_id=user_id,
            vector=vector,
            big_five=avg_bf,
            emotions=avg_em,
            fingerprint_hash=fp_hash,
            source_window_count=len(texts),
        )

        # Check drift alert
        drift_alert = self.vault.check_drift_alert(user_id)

        summary = {
            "row_id": row_id,
            "big_five": avg_bf,
            "emotions": avg_em,
            "vector_norm": float(sum(v * v for v in vector) ** 0.5),
            "fingerprint": fp_hash,
            "drift_alert": drift_alert,
        }

        if drift_alert:
            logger.warning(f"Drift alert triggered for user {user_id}!")

        return summary

    def get_status(self, user_id: str) -> dict | None:
        profile = self.vault.get_latest_profile(user_id)
        if profile is None:
            return None
        drift_history = self.vault.get_drift_history(user_id, limit=5)
        return {
            "profile": profile,
            "drift_history": drift_history,
            "drift_alert": self.vault.check_drift_alert(user_id),
        }
