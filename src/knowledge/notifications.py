"""
Notification system for soul-avatar-matcher.

Handles alerts for:
- Knowledge base updates (new papers found)
- Personality drift alerts
- Match consent notifications
- System health events

Supports console, log file, and optional webhook delivery.
"""

from __future__ import annotations

import os
import json
import time
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import httpx

from config.settings import settings


class NotificationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"


@dataclass
class Notification:
    level: NotificationLevel
    category: str
    title: str
    body: str
    timestamp: float = field(default_factory=time.time)
    dismissed: bool = False


class NotificationService:
    def __init__(self, notification_file: str | None = None):
        self._notifications: list[Notification] = []
        self._notification_file = notification_file or str(
            settings.PROJECT_ROOT / "data" / "notifications.json"
        )
        self._webhook_url = os.environ.get("SOUL_AVATAR_WEBHOOK_URL", "")
        self._load()

    def _load(self):
        try:
            if os.path.exists(self._notification_file):
                with open(self._notification_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._notifications = [
                        Notification(
                            level=NotificationLevel(n["level"]),
                            category=n["category"],
                            title=n["title"],
                            body=n["body"],
                            timestamp=n["timestamp"],
                            dismissed=n.get("dismissed", False),
                        )
                        for n in data
                    ]
        except Exception:
            self._notifications = []

    def _save(self):
        os.makedirs(os.path.dirname(self._notification_file), exist_ok=True)
        with open(self._notification_file, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "level": n.level.value,
                        "category": n.category,
                        "title": n.title,
                        "body": n.body,
                        "timestamp": n.timestamp,
                        "dismissed": n.dismissed,
                    }
                    for n in self._notifications[-500:]
                ],
                f,
                indent=2,
            )

    def notify(
        self,
        level: NotificationLevel,
        category: str,
        title: str,
        body: str,
    ) -> Notification:
        n = Notification(level=level, category=category, title=title, body=body)
        self._notifications.append(n)
        self._save()

        log_fn = {
            NotificationLevel.INFO: logger.info,
            NotificationLevel.WARNING: logger.warning,
            NotificationLevel.ALERT: logger.error,
        }.get(level, logger.info)
        log_fn(f"[{category}] {title}: {body}")

        self._send_webhook(n)
        return n

    def notify_knowledge_update(self, num_papers: int, papers: list[dict] | None = None):
        self.notify(
            level=NotificationLevel.INFO,
            category="knowledge",
            title=f"Knowledge base updated: {num_papers} new papers",
            body=(
                f"{num_papers} new relevant papers found and added to SECOND-KNOWLEDGE-BRAIN.md.\n"
                + "\n".join(f"  - {p.get('title', 'Unknown')[:80]}" for p in (papers or [])[:5])
                if papers else ""
            ),
        )

    def notify_drift_alert(self, user_id: str, delta: float):
        self.notify(
            level=NotificationLevel.ALERT,
            category="personality_drift",
            title=f"Personality drift detected for user {user_id}",
            body=f"Drift delta: {delta:.4f} exceeds threshold {settings.DRIFT_ALERT_THRESHOLD}. Consider reviewing recent behavioral data.",
        )

    def notify_match_consent(self, match_id: str, status: str):
        level = NotificationLevel.INFO if status == "confirmed" else NotificationLevel.WARNING
        self.notify(
            level=level,
            category="match_consent",
            title=f"Match {match_id}: {status}",
            body=f"Match {match_id} {status}. Check consent gate for details.",
        )

    def notify_system_health(self, component: str, healthy: bool, detail: str = ""):
        self.notify(
            level=NotificationLevel.WARNING if not healthy else NotificationLevel.INFO,
            category="system_health",
            title=f"{'✓' if healthy else '✗'} {component}: {'healthy' if healthy else 'unavailable'}",
            body=detail,
        )

    def get_unread(self, category: str | None = None) -> list[Notification]:
        notifications = self._notifications
        if category:
            notifications = [n for n in notifications if n.category == category]
        return [n for n in notifications if not n.dismissed]

    def dismiss(self, index: int) -> bool:
        if 0 <= index < len(self._notifications):
            self._notifications[index].dismissed = True
            self._save()
            return True
        return False

    def dismiss_all(self, category: str | None = None):
        for n in self._notifications:
            if category is None or n.category == category:
                n.dismissed = True
        self._save()

    def _send_webhook(self, notification: Notification):
        if not self._webhook_url:
            return
        try:
            httpx.post(
                self._webhook_url,
                json={
                    "level": notification.level.value,
                    "category": notification.category,
                    "title": notification.title,
                    "body": notification.body,
                    "timestamp": notification.timestamp,
                },
                timeout=5,
            )
        except Exception:
            pass


notification_service = NotificationService()
