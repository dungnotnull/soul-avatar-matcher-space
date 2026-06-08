"""
FastAPI REST API backend for soul-avatar-matcher.

Provides endpoints for:
- Match list/status queries
- Personality profile retrieval
- Consent gate operations
- System health checks
- Knowledge update triggering
- Notification retrieval
"""

from __future__ import annotations

from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from config.settings import settings
from src.vault.manager import PersonalityVaultManager
from src.personality.updater import PersonalityUpdater
from src.consent.gate import ConsentGate
from src.reports.generator import validate_config
from src.a2a.slm_reasoner import LocalSLMReasoner
from src.knowledge.notifications import notification_service, NotificationLevel


app = FastAPI(
    title="soul-avatar-matcher API",
    description="Privacy-first cognitive compatibility engine REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vault = PersonalityVaultManager()
updater = PersonalityUpdater()
consent_gate = ConsentGate()
reasoner = LocalSLMReasoner()


class MatchStatusResponse(BaseModel):
    match_id: str
    compatibility_score: float
    self_confirmed: bool
    other_confirmed: bool
    is_bilateral: bool
    expires_at: int


class PersonalityProfileResponse(BaseModel):
    user_id: str
    big_five: dict[str, float]
    emotions: dict[str, float]
    drift_delta: float
    drift_alert: bool
    last_updated: int


class ConsentRequest(BaseModel):
    match_id: str
    user_id: str
    confirmed: bool


class ConsentResponse(BaseModel):
    matched: bool
    message: str
    compatibility_score: float


class HealthResponse(BaseModel):
    ollama: bool
    providers: dict[str, bool | str]
    db_path: str
    grpc_host: str
    compatibility_threshold: float


class NotificationItem(BaseModel):
    level: str
    category: str
    title: str
    body: str
    timestamp: float
    dismissed: bool


class KnowledgeUpdateRequest(BaseModel):
    dry_run: bool = False


@app.get("/health", response_model=HealthResponse)
async def health_check():
    config = validate_config()
    return HealthResponse(
        ollama=reasoner.health_check(),
        providers=config,
        db_path=str(settings.db_path_absolute),
        grpc_host=settings.GRPC_HOST,
        compatibility_threshold=settings.COMPATIBILITY_THRESHOLD,
    )


@app.get("/matches", response_model=list[MatchStatusResponse])
async def list_matches(
    user_id: str = Query(..., description="User ID to filter matches for"),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        rows = vault.conn.execute(
            """SELECT * FROM pending_matches
               WHERE (self_user_id = ? OR other_avatar_id = ?)
               AND expires_at > ?
               ORDER BY compatibility_score DESC
               LIMIT ?""",
            (user_id, user_id, int(datetime.now().timestamp()), limit),
        ).fetchall()
    except Exception as e:
        logger.error(f"Match query failed: {e}")
        raise HTTPException(status_code=500, detail="Database error — check SQLCipher key.")

    return [
        MatchStatusResponse(
            match_id=r["match_id"],
            compatibility_score=r["compatibility_score"],
            self_confirmed=bool(r["self_confirmed"]),
            other_confirmed=bool(r["other_confirmed"]),
            is_bilateral=bool(r["self_confirmed"] and r["other_confirmed"]),
            expires_at=r["expires_at"],
        )
        for r in rows
    ]


@app.get("/matches/{match_id}", response_model=MatchStatusResponse)
async def get_match(match_id: str):
    status = consent_gate.check_match_status(match_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Match not found or expired.")
    return MatchStatusResponse(**status)


@app.get("/matches/{match_id}/report")
async def get_match_report(match_id: str, user_id: str = Query(...)):
    report = consent_gate.get_anonymized_report(match_id, user_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return {"match_id": match_id, "user_id": user_id, "report": report}


@app.post("/consent", response_model=ConsentResponse)
async def submit_consent(request: ConsentRequest):
    result = consent_gate.process_decision(
        session_id=request.match_id,
        avatar_id=request.user_id,
        confirmed=request.confirmed,
    )
    notification_service.notify_match_consent(
        match_id=request.match_id,
        status="confirmed" if request.confirmed else "rejected",
    )
    return ConsentResponse(**result)


@app.get("/profile/{user_id}", response_model=PersonalityProfileResponse)
async def get_profile(user_id: str):
    status = updater.get_status(user_id)
    if status is None:
        raise HTTPException(status_code=404, detail="No personality data found.")
    profile = status["profile"]
    return PersonalityProfileResponse(
        user_id=user_id,
        big_five={
            "openness": profile["big_five_o"],
            "conscientiousness": profile["big_five_c"],
            "extraversion": profile["big_five_e"],
            "agreeableness": profile["big_five_a"],
            "neuroticism": profile["big_five_n"],
        },
        emotions={
            "joy": profile["emotion_joy"],
            "sadness": profile["emotion_sadness"],
            "anger": profile["emotion_anger"],
            "fear": profile["emotion_fear"],
            "surprise": profile["emotion_surprise"],
            "disgust": profile["emotion_disgust"],
            "neutral": profile["emotion_neutral"],
        },
        drift_delta=profile["drift_delta"],
        drift_alert=status["drift_alert"],
        last_updated=profile["created_at"],
    )


@app.get("/notifications", response_model=list[NotificationItem])
async def list_notifications(
    category: str | None = None,
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
):
    notes = notification_service._notifications
    if category:
        notes = [n for n in notes if n.category == category]
    if unread_only:
        notes = [n for n in notes if not n.dismissed]
    notes = list(reversed(notes[-limit:]))
    return [
        NotificationItem(
            level=n.level.value,
            category=n.category,
            title=n.title,
            body=n.body,
            timestamp=n.timestamp,
            dismissed=n.dismissed,
        )
        for n in notes
    ]


@app.post("/notifications/dismiss")
async def dismiss_notifications(category: str | None = None):
    notification_service.dismiss_all(category)
    notification_service._save()
    return {"dismissed": True, "category": category}


@app.post("/knowledge/update")
async def trigger_knowledge_update(request: KnowledgeUpdateRequest = None):
    from scripts.weekly_knowledge_update import main as wk_main
    wk_main()
    return {"status": "completed"}


@app.post("/drift/check/{user_id}")
async def check_drift(user_id: str):
    alert = vault.check_drift_alert(user_id)
    status = updater.get_status(user_id)
    return {
        "user_id": user_id,
        "drift_alert": alert,
        "drift_delta": status["profile"]["drift_delta"] if status else None,
        "threshold": settings.DRIFT_ALERT_THRESHOLD,
    }
