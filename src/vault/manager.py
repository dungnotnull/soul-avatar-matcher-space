"""
Encrypted personality vault manager using SQLCipher AES-256.

Stores/retrieves personality vectors, Big Five scores, emotion distributions,
vector history for drift tracking, and pending match records.
"""

from __future__ import annotations

import sqlite3
import time
import struct
import numpy as np
from pathlib import Path
from loguru import logger

from config.settings import settings
from src.vault.schema import get_schema


class PersonalityVaultManager:
    def __init__(self, db_path: str | Path | None = None, key: str | None = None):
        self.db_path = str(db_path or settings.db_path_absolute)
        self.key = key or settings.SQLCIPHER_KEY
        self._conn: sqlite3.Connection | None = None
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute(f"PRAGMA key='{self.key}'")
            self._conn.execute("PRAGMA cipher_compatibility = 4")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _vector_to_blob(self, vector: np.ndarray) -> bytes:
        return struct.pack(f"{len(vector)}d", *vector.astype(np.float64))

    def _blob_to_vector(self, blob: bytes) -> np.ndarray:
        count = len(blob) // 8
        return np.array(struct.unpack(f"{count}d", blob), dtype=np.float64)

    def initialize(self):
        logger.info("Initializing personality vault schema...")
        self.conn.executescript(get_schema())
        self.conn.commit()
        logger.info("Vault schema initialized (v0).")

    def ensure_user(self, user_id: str) -> None:
        now = int(time.time())
        self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, created_at, updated_at, is_active) VALUES (?, ?, ?, 1)",
            (user_id, now, now),
        )
        self.conn.commit()

    def store_vector(
        self,
        user_id: str,
        vector: np.ndarray,
        big_five: dict[str, float],
        emotions: dict[str, float],
        fingerprint_hash: str,
        source_window_count: int,
    ) -> int:
        self.ensure_user(user_id)
        now = int(time.time())

        # Get previous vector for drift calculation
        prev = self.get_latest_vector(user_id)
        drift_delta = 0.0
        if prev is not None:
            drift_delta = float(1.0 - np.dot(vector, prev) / (np.linalg.norm(vector) * np.linalg.norm(prev) + 1e-8))

        blob = self._vector_to_blob(vector)

        cursor = self.conn.execute(
            """INSERT INTO personality_vectors
               (user_id, vector_blob, big_five_o, big_five_c, big_five_e, big_five_a, big_five_n,
                emotion_joy, emotion_sadness, emotion_anger, emotion_fear, emotion_surprise, emotion_disgust, emotion_neutral,
                drift_delta, fingerprint_hash, source_window_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, blob,
                big_five.get("openness", 0), big_five.get("conscientiousness", 0),
                big_five.get("extraversion", 0), big_five.get("agreeableness", 0),
                big_five.get("neuroticism", 0),
                emotions.get("joy", 0), emotions.get("sadness", 0),
                emotions.get("anger", 0), emotions.get("fear", 0),
                emotions.get("surprise", 0), emotions.get("disgust", 0),
                emotions.get("neutral", 0),
                drift_delta, fingerprint_hash, source_window_count, now,
            ),
        )

        if prev is not None and drift_delta > 0:
            self.conn.execute(
                "INSERT INTO vector_history (user_id, previous_vector_blob, new_vector_blob, drift_delta, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, self._vector_to_blob(prev), blob, drift_delta, now),
            )

        self.conn.execute("UPDATE users SET updated_at = ? WHERE user_id = ?", (now, user_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_latest_vector(self, user_id: str) -> np.ndarray | None:
        row = self.conn.execute(
            "SELECT vector_blob FROM personality_vectors WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return self._blob_to_vector(row["vector_blob"])

    def get_latest_profile(self, user_id: str) -> dict | None:
        row = self.conn.execute(
            """SELECT * FROM personality_vectors
               WHERE user_id = ? ORDER BY created_at DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_drift_history(self, user_id: str, limit: int = 30) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM vector_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def check_drift_alert(self, user_id: str) -> bool:
        row = self.conn.execute(
            "SELECT drift_delta FROM personality_vectors WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if row is None:
            return False
        return row["drift_delta"] > settings.DRIFT_ALERT_THRESHOLD

    def store_pending_match(
        self,
        match_id: str,
        self_user_id: str,
        other_avatar_id: str,
        compatibility_score: float,
        anonymized_report: str,
        ttl_seconds: int = 604800,
    ) -> None:
        now = int(time.time())
        self.conn.execute(
            """INSERT OR REPLACE INTO pending_matches
               (match_id, self_user_id, other_avatar_id, compatibility_score, anonymized_report,
                self_confirmed, other_confirmed, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)""",
            (match_id, self_user_id, other_avatar_id, compatibility_score, anonymized_report, now, now + ttl_seconds),
        )
        self.conn.commit()

    def get_pending_match(self, match_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM pending_matches WHERE match_id = ? AND expires_at > ?",
            (match_id, int(time.time())),
        ).fetchone()
        return dict(row) if row else None

    def confirm_match(self, match_id: str, user_id: str) -> bool:
        match = self.get_pending_match(match_id)
        if match is None:
            logger.warning(f"Pending match {match_id} not found or expired.")
            return False

        column = "self_confirmed" if match["self_user_id"] == user_id else "other_confirmed"
        self.conn.execute(
            f"UPDATE pending_matches SET {column} = 1 WHERE match_id = ?",
            (match_id,),
        )
        self.conn.execute(
            "INSERT INTO consent_log (match_id, user_id, action, created_at) VALUES (?, ?, 'confirmed', ?)",
            (match_id, user_id, int(time.time())),
        )

        # Check bilateral
        refreshed = self.get_pending_match(match_id)
        if refreshed and refreshed["self_confirmed"] and refreshed["other_confirmed"]:
            self.conn.commit()
            return True
        self.conn.commit()
        return False

    def reject_match(self, match_id: str, user_id: str) -> None:
        self.conn.execute(
            "INSERT INTO consent_log (match_id, user_id, action, created_at) VALUES (?, ?, 'rejected', ?)",
            (match_id, user_id, int(time.time())),
        )
        self.conn.execute("DELETE FROM pending_matches WHERE match_id = ?", (match_id,))
        self.conn.commit()

    def expire_stale_matches(self) -> int:
        now = int(time.time())
        cursor = self.conn.execute("DELETE FROM pending_matches WHERE expires_at <= ?", (now,))
        self.conn.commit()
        return cursor.rowcount
