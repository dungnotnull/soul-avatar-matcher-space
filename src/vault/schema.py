"""
SQLite schema for Personality Vault (v0 migration).

Tables store encrypted personality data using SQLCipher AES-256.
This module provides the schema definition and migration runner.
"""

from __future__ import annotations

SCHEMA_V0 = """

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS personality_vectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    vector_blob BLOB NOT NULL,              -- 512 float64 values serialized
    big_five_o REAL NOT NULL,
    big_five_c REAL NOT NULL,
    big_five_e REAL NOT NULL,
    big_five_a REAL NOT NULL,
    big_five_n REAL NOT NULL,
    emotion_joy REAL NOT NULL DEFAULT 0,
    emotion_sadness REAL NOT NULL DEFAULT 0,
    emotion_anger REAL NOT NULL DEFAULT 0,
    emotion_fear REAL NOT NULL DEFAULT 0,
    emotion_surprise REAL NOT NULL DEFAULT 0,
    emotion_disgust REAL NOT NULL DEFAULT 0,
    emotion_neutral REAL NOT NULL DEFAULT 0,
    drift_delta REAL NOT NULL DEFAULT 0,
    fingerprint_hash TEXT NOT NULL,
    source_window_count INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS vector_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    previous_vector_blob BLOB,
    new_vector_blob BLOB NOT NULL,
    drift_delta REAL NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS pending_matches (
    match_id TEXT PRIMARY KEY,
    self_user_id TEXT NOT NULL,
    other_avatar_id TEXT NOT NULL,
    compatibility_score REAL NOT NULL,
    anonymized_report TEXT NOT NULL,
    self_confirmed INTEGER NOT NULL DEFAULT 0,
    other_confirmed INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    FOREIGN KEY (self_user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS consent_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,                   -- 'confirmed' or 'rejected'
    created_at INTEGER NOT NULL,
    FOREIGN KEY (match_id) REFERENCES pending_matches(match_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_vectors_user ON personality_vectors(user_id);
CREATE INDEX IF NOT EXISTS idx_vectors_created ON personality_vectors(created_at);
CREATE INDEX IF NOT EXISTS idx_history_user ON vector_history(user_id);
CREATE INDEX IF NOT EXISTS idx_matches_self ON pending_matches(self_user_id);
CREATE INDEX IF NOT EXISTS idx_matches_expires ON pending_matches(expires_at);
CREATE INDEX IF NOT EXISTS idx_consent_match ON consent_log(match_id);

PRAGMA user_version = 0;
"""


def get_schema() -> str:
    return SCHEMA_V0
