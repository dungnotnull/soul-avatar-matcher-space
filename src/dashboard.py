"""
Streamlit web dashboard for soul-avatar-matcher match review.

Provides:
- Match overview with compatibility scores
- Personality profile comparison radar charts
- Consent gate interface
- Notification center
- System health status
"""

from __future__ import annotations

import numpy as np
import streamlit as st
import pandas as pd
from datetime import datetime

from config.settings import settings
from src.vault.manager import PersonalityVaultManager
from src.personality.updater import PersonalityUpdater
from src.consent.gate import ConsentGate
from src.reports.generator import ReportGenerator, validate_config
from src.knowledge.notifications import notification_service, NotificationLevel


st.set_page_config(
    page_title="soul-avatar-matcher",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar():
    with st.sidebar:
        st.title("🕊️ Soul Avatar Matcher")
        st.caption("Privacy-first cognitive compatibility")
        st.divider()

        page = st.radio(
            "Navigate",
            ["Match Review", "Personality Profiles", "Consent Gate", "Notifications", "System Health"],
            label_visibility="collapsed",
        )
        st.divider()
        st.metric("Compatibility Threshold", f"{settings.COMPATIBILITY_THRESHOLD:.0%}")
        st.metric("Vector/Conversation Weight", f"{settings.VECTOR_WEIGHT:.0%}/{settings.DIALOGUE_WEIGHT:.0%}")
    return page


def render_match_review():
    st.header("Match Review")
    vault = PersonalityVaultManager()

    try:
        matches = vault.conn.execute(
            "SELECT * FROM pending_matches WHERE expires_at > ? ORDER BY compatibility_score DESC",
            (int(datetime.now().timestamp()),),
        ).fetchall()
    except Exception:
        st.info("No encrypted database available. The vault requires SQLCipher with a valid key.")
        return

    if not matches:
        st.info("No pending matches found. Run A2A sessions to generate matches.")
        return

    df = pd.DataFrame(
        [
            {
                "Match ID": m["match_id"][:8] + "...",
                "Score": f"{m['compatibility_score']:.2%}",
                "User A": m["self_user_id"][:8],
                "User B": m["other_avatar_id"][:8],
                "Bilateral": "✅" if (m["self_confirmed"] and m["other_confirmed"]) else "⏳",
                "Expires": datetime.fromtimestamp(m["expires_at"]).strftime("%Y-%m-%d"),
            }
            for m in matches
        ]
    )

    st.dataframe(df, use_container_width=True, hide_index=True)

    selected = st.selectbox("Select match to view", [m["match_id"] for m in matches])
    if selected:
        match = next(m for m in matches if m["match_id"] == selected)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Compatibility Report")
            st.text_area("Report", match["anonymized_report"][:1000], height=250, disabled=True)
        with col2:
            st.metric("Score", f"{match['compatibility_score']:.2%}")
            st.metric("Bilateral Confirmed", "✅" if (match["self_confirmed"] and match["other_confirmed"]) else "❌")
            st.metric("Expires", datetime.fromtimestamp(match["expires_at"]).strftime("%Y-%m-%d %H:%M"))


def render_personality_profiles():
    st.header("Personality Profiles")
    user_id = st.text_input("Enter User ID to view profile")

    if user_id:
        updater = PersonalityUpdater()
        status = updater.get_status(user_id)
        if status is None:
            st.warning(f"No personality data found for user {user_id}")
            return

        profile = status["profile"]
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Big Five (OCEAN)")
            traits = {
                "Openness": profile["big_five_o"],
                "Conscientiousness": profile["big_five_c"],
                "Extraversion": profile["big_five_e"],
                "Agreeableness": profile["big_five_a"],
                "Neuroticism": profile["big_five_n"],
            }
            df = pd.DataFrame({"Trait": list(traits.keys()), "Score": list(traits.values())})
            st.bar_chart(df.set_index("Trait"), use_container_width=True)

        with col2:
            st.subheader("Emotion Baseline")
            emotions = {
                "Joy": profile["emotion_joy"],
                "Sadness": profile["emotion_sadness"],
                "Anger": profile["emotion_anger"],
                "Fear": profile["emotion_fear"],
                "Surprise": profile["emotion_surprise"],
                "Disgust": profile["emotion_disgust"],
                "Neutral": profile["emotion_neutral"],
            }
            df_em = pd.DataFrame({"Emotion": list(emotions.keys()), "Score": list(emotions.values())})
            st.bar_chart(df_em.set_index("Emotion"), use_container_width=True)

        st.metric("Drift Delta", f"{profile['drift_delta']:.4f}")
        if status["drift_alert"]:
            st.error(f"⚠ Drift alert triggered! Delta exceeds threshold {settings.DRIFT_ALERT_THRESHOLD}")


def render_consent_gate():
    st.header("Consent Gate")
    gate = ConsentGate()
    match_id = st.text_input("Match ID")

    if match_id:
        status = gate.check_match_status(match_id)
        if status is None:
            st.error("Match not found or expired.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Score", f"{status['compatibility_score']:.2%}")
            st.metric("User A Confirmed", "✅" if status["self_confirmed"] else "⏳")
        with col2:
            st.metric("Bilateral", "✅" if status["is_bilateral"] else "⏳")
            st.metric("Other Confirmed", "✅" if status["other_confirmed"] else "⏳")

        if status["is_bilateral"]:
            st.success("🎉 Both parties confirmed! Contact information can now be revealed.")
        else:
            user_id = st.text_input("Your User ID", key="consent_user")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Confirm Match", type="primary"):
                    result = gate.process_decision(match_id, user_id, True)
                    st.info(result["message"])
            with col_b:
                if st.button("❌ Reject Match", type="secondary"):
                    result = gate.process_decision(match_id, user_id, False)
                    st.info(result["message"])


def render_notifications():
    st.header("Notifications")
    category_filter = st.selectbox("Filter by category", ["all", "knowledge", "personality_drift", "match_consent", "system_health"])

    notifications = notification_service._notifications
    if category_filter != "all":
        notifications = [n for n in notifications if n.category == category_filter]

    notifications = list(reversed(notifications[-50:]))

    if not notifications:
        st.info("No notifications.")
        return

    for i, n in enumerate(notifications):
        level_icon = {"info": "ℹ️", "warning": "⚠️", "alert": "🔴"}.get(n.level.value, "•")
        with st.container():
            cols = st.columns([1, 20, 2])
            cols[0].markdown(level_icon)
            cols[1].markdown(f"**{n.title}**  \n*{datetime.fromtimestamp(n.timestamp).strftime('%Y-%m-%d %H:%M')} — {n.category}*  \n{n.body}")
            if not n.dismissed:
                if cols[2].button("✕", key=f"dismiss_{i}"):
                    notification_service.dismiss(n)
                    st.rerun()
        st.divider()

    if st.button("Dismiss All", type="secondary"):
        notification_service.dismiss_all(category_filter if category_filter != "all" else None)
        st.rerun()


def render_system_health():
    st.header("System Health")
    config = validate_config()
    cols = st.columns(3)
    with cols[0]:
        status = "✅" if config.get("claude") is True else "❌"
        st.metric("Claude API", status, delta=str(config.get("claude", "unknown")))
    with cols[1]:
        status = "✅" if config.get("openai") is True else "❌"
        st.metric("OpenAI API", status, delta=str(config.get("openai", "unknown")))
    with cols[2]:
        status = "✅" if config.get("ollama") is True else "❌"
        st.metric("Ollama (Local)", status, delta="connected" if config.get("ollama") else "unreachable")

    st.divider()
    st.subheader("Configuration")
    st.json({
        "compatibility_threshold": settings.COMPATIBILITY_THRESHOLD,
        "vector_weight": settings.VECTOR_WEIGHT,
        "dialogue_weight": settings.DIALOGUE_WEIGHT,
        "drift_alert_threshold": settings.DRIFT_ALERT_THRESHOLD,
        "ollama_model": settings.OLLAMA_MODEL,
        "grpc_host": settings.GRPC_HOST,
        "db_path": str(settings.db_path_absolute),
    })


def main():
    page = render_sidebar()
    if page == "Match Review":
        render_match_review()
    elif page == "Personality Profiles":
        render_personality_profiles()
    elif page == "Consent Gate":
        render_consent_gate()
    elif page == "Notifications":
        render_notifications()
    elif page == "System Health":
        render_system_health()


if __name__ == "__main__":
    main()
