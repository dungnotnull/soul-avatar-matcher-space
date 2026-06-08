"""
Consent gate — bilateral confirmation flow for match reveal.

Generates anonymized compatibility report, stores pending matches,
and enforces that both parties must confirm before contact info is revealed.
"""

from __future__ import annotations

import uuid
import time
from loguru import logger

from proto.avatar_pb2 import AvatarCapsule
from src.vault.manager import PersonalityVaultManager
from src.reports.generator import ReportGenerator
from config.settings import settings


class ConsentGate:
    """
    Manages the consent workflow:
    1. Generates anonymized compatibility report
    2. Stores pending match in encrypted vault
    3. Requires bilateral confirmation before revealing contact
    """

    def __init__(
        self,
        vault: PersonalityVaultManager | None = None,
        report_generator: ReportGenerator | None = None,
    ):
        self.vault = vault or PersonalityVaultManager()
        self.report_generator = report_generator or ReportGenerator()
        self._pending_decisions: dict[str, dict] = {}

    def initiate_match(
        self,
        capsule_a: AvatarCapsule,
        capsule_b: AvatarCapsule,
        compatibility_score: float,
        ttl_seconds: int = 604800,
    ) -> str:
        """
        Create a pending match record requiring bilateral consent.
        Returns match_id.
        """
        match_id = str(uuid.uuid4())

        report_a = self.report_generator.generate(
            self_capsule=capsule_a,
            other_capsule=capsule_b,
            compatibility_score=compatibility_score,
            recipient_id=capsule_a.avatar_id,
        )

        report_b = self.report_generator.generate(
            self_capsule=capsule_b,
            other_capsule=capsule_a,
            compatibility_score=compatibility_score,
            recipient_id=capsule_b.avatar_id,
        )

        self.vault.store_pending_match(
            match_id=match_id,
            self_user_id=capsule_a.avatar_id,
            other_avatar_id=capsule_b.avatar_id,
            compatibility_score=compatibility_score,
            anonymized_report=report_a,
            ttl_seconds=ttl_seconds,
        )

        self._pending_decisions[match_id] = {
            "capsule_a": capsule_a,
            "capsule_b": capsule_b,
            "score": compatibility_score,
            "report_a": report_a,
            "report_b": report_b,
            "a_confirmed": False,
            "b_confirmed": False,
        }

        logger.info(f"Pending match {match_id} created: score={compatibility_score:.4f}")
        return match_id

    def get_anonymized_report(self, match_id: str, user_id: str) -> str | None:
        """Retrieve the anonymized report for a specific user."""
        match = self.vault.get_pending_match(match_id)
        if match is None:
            return None

        if match["self_user_id"] == user_id:
            return match["anonymized_report"]

        pending = self._pending_decisions.get(match_id)
        if pending and pending["capsule_b"].avatar_id == user_id:
            return pending["report_b"]

        return None

    def process_decision(
        self,
        session_id: str,
        avatar_id: str,
        confirmed: bool,
    ) -> dict:
        """
        Process a user's match decision.
        Returns status dict with matched flag and message.
        """
        match_id = session_id
        match = self.vault.get_pending_match(match_id)
        if match is None:
            match_id = self._find_match_for_session(session_id)
            if match_id:
                match = self.vault.get_pending_match(match_id)

        if match is None:
            return {"matched": False, "message": "Match not found or expired."}

        if not confirmed:
            self.vault.reject_match(match_id, avatar_id)
            self._pending_decisions.pop(match_id, None)
            logger.info(f"Match {match_id} rejected by {avatar_id}")
            return {"matched": False, "message": "Match rejected."}

        is_bilateral = self.vault.confirm_match(match_id, avatar_id)

        if is_bilateral:
            logger.info(f"Match {match_id} confirmed bilaterally! Contact reveal authorized.")
            return {
                "matched": True,
                "message": "Both parties confirmed! Contact information can now be revealed.",
                "compatibility_score": match["compatibility_score"],
            }
        else:
            logger.info(f"Match {match_id}: {avatar_id} confirmed. Awaiting other party.")
            return {
                "matched": False,
                "message": "Your confirmation has been recorded. Awaiting the other person's decision.",
                "compatibility_score": match["compatibility_score"],
            }

    def _find_match_for_session(self, session_id: str) -> str | None:
        """Try to match a session_id to a pending match via stored decisions."""
        for mid, data in self._pending_decisions.items():
            if data.get("session_id") == session_id:
                return mid
        return None

    def check_match_status(self, match_id: str) -> dict | None:
        match = self.vault.get_pending_match(match_id)
        if match is None:
            return None
        return {
            "match_id": match["match_id"],
            "compatibility_score": match["compatibility_score"],
            "self_confirmed": bool(match["self_confirmed"]),
            "other_confirmed": bool(match["other_confirmed"]),
            "is_bilateral": bool(match["self_confirmed"] and match["other_confirmed"]),
            "expires_at": match["expires_at"],
        }

    def expire_stale(self) -> int:
        return self.vault.expire_stale_matches()
