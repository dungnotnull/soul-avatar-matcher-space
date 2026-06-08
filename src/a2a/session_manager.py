"""
A2A Session Manager — orchestrates multi-round debates between two avatar capsules.

Manages the debate lifecycle: initiation, turn sequencing, topic transitions,
and transcript collection for compatibility scoring.
"""

from __future__ import annotations

import uuid
import time
from loguru import logger

from proto.avatar_pb2 import AvatarCapsule
from src.a2a.debate_topics import get_topic, get_default_topics
from src.a2a.slm_reasoner import LocalSLMReasoner


class A2ASession:
    def __init__(
        self,
        session_id: str,
        capsule_a: AvatarCapsule,
        capsule_b: AvatarCapsule,
        topic_ids: list[str],
        max_rounds: int = 2,
    ):
        self.session_id = session_id
        self.capsule_a = capsule_a
        self.capsule_b = capsule_b
        self.topic_ids = topic_ids
        self.max_rounds = max_rounds
        self.transcript: list[dict] = []
        self.current_topic_idx = 0
        self.current_round = 0
        self.is_complete = False
        self.created_at = int(time.time())

    @property
    def current_topic_id(self) -> str | None:
        if self.current_topic_idx < len(self.topic_ids):
            return self.topic_ids[self.current_topic_idx]
        return None

    def add_turn(self, speaker_id: str, content: str, topic_id: str, round_num: int, is_final: bool = False):
        self.transcript.append({
            "speaker_id": speaker_id,
            "content": content,
            "topic_id": topic_id,
            "round": round_num,
            "timestamp": int(time.time()),
        })
        if is_final:
            self.is_complete = True


class A2ASessionManager:
    """
    Orchestrates A2A debate sessions between two avatars.
    Generates avatar responses using the local SLM reasoner.
    """

    def __init__(self, reasoner: LocalSLMReasoner | None = None):
        self.reasoner = reasoner or LocalSLMReasoner()
        self._sessions: dict[str, A2ASession] = {}

    def create_session(
        self,
        capsule_a: AvatarCapsule,
        capsule_b: AvatarCapsule,
        topic_ids: list[str] | None = None,
        max_rounds: int = 2,
    ) -> A2ASession:
        session_id = str(uuid.uuid4())
        topics = topic_ids or get_default_topics()
        session = A2ASession(session_id, capsule_a, capsule_b, topics, max_rounds)
        self._sessions[session_id] = session
        logger.info(f"Created A2A session {session_id} with {len(topics)} topics")
        return session

    def get_session(self, session_id: str) -> A2ASession | None:
        return self._sessions.get(session_id)

    def run_debate(self, session: A2ASession) -> list[dict]:
        """
        Run a complete debate between two avatar capsules.
        Returns the full transcript.
        """
        logger.info(f"Starting debate for session {session.session_id}")

        for topic_idx, topic_id in enumerate(session.topic_ids):
            topic = get_topic(topic_id)
            if topic is None:
                logger.warning(f"Unknown topic: {topic_id}, skipping.")
                continue

            logger.info(f"Topic {topic_idx+1}/{len(session.topic_ids)}: {topic['title']}")

            for rnd in range(session.max_rounds):
                is_final = (topic_idx == len(session.topic_ids) - 1 and rnd == session.max_rounds - 1)

                # Avatar A's turn
                prompt = self._build_prompt(session.capsule_a, topic, "prompt_a" if rnd == 0 else "prompt_b", session)
                response_a = self.reasoner.debate_response(
                    topic=topic["title"],
                    personality_context=self._personality_snapshot(session.capsule_a),
                    previous_turns=[t["content"] for t in session.transcript],
                )
                session.add_turn(session.capsule_a.avatar_id, response_a, topic_id, rnd, is_final)

                # Avatar B's turn
                response_b = self.reasoner.debate_response(
                    topic=topic["title"],
                    personality_context=self._personality_snapshot(session.capsule_b),
                    previous_turns=[t["content"] for t in session.transcript],
                )
                session.add_turn(session.capsule_b.avatar_id, response_b, topic_id, rnd, is_final)

                if is_final:
                    break

        logger.info(f"Debate complete for session {session.session_id}: {len(session.transcript)} turns")
        return session.transcript

    def _build_prompt(
        self,
        capsule: AvatarCapsule,
        topic: dict,
        prompt_key: str,
        session: A2ASession,
    ) -> str:
        return topic.get(prompt_key, topic.get("prompt_a", "Share your thoughts on this topic."))

    def _personality_snapshot(self, capsule: AvatarCapsule) -> str:
        bf = capsule.big_five
        return (
            f"Big Five traits: Openness={bf.openness:.2f}, "
            f"Conscientiousness={bf.conscientiousness:.2f}, "
            f"Extraversion={bf.extraversion:.2f}, "
            f"Agreeableness={bf.agreeableness:.2f}, "
            f"Neuroticism={bf.neuroticism:.2f}."
        )

    async def run_debate_stream(self, session: A2ASession):
        """
        Run a complete debate as an async generator, yielding DebateTurn protos
        in real-time as each avatar responds. Tokens stream as they're generated
        by the SLM, so the client sees the response build up word by word.
        """
        from proto.a2a_session_pb2 import DebateTurn

        logger.info(f"Starting streaming debate for session {session.session_id}")

        for topic_idx, topic_id in enumerate(session.topic_ids):
            topic = get_topic(topic_id)
            if topic is None:
                logger.warning(f"Unknown topic: {topic_id}, skipping.")
                continue

            logger.info(f"Topic {topic_idx+1}/{len(session.topic_ids)}: {topic['title']}")

            for rnd in range(session.max_rounds):
                is_final = (
                    topic_idx == len(session.topic_ids) - 1
                    and rnd == session.max_rounds - 1
                )

                # --- Avatar A's turn (streaming) ---
                full_a = ""
                async for chunk in self.reasoner.debate_response_stream(
                    topic=topic["title"],
                    personality_context=self._personality_snapshot(session.capsule_a),
                    previous_turns=[t["content"] for t in session.transcript],
                ):
                    if not chunk:
                        continue
                    full_a += chunk
                    yield DebateTurn(
                        session_id=session.session_id,
                        topic_id=topic_id,
                        round=rnd,
                        speaker_avatar_id=session.capsule_a.avatar_id,
                        content=chunk,
                        is_final=False,
                    )

                # Signal that this avatar's turn is complete
                yield DebateTurn(
                    session_id=session.session_id,
                    topic_id=topic_id,
                    round=rnd,
                    speaker_avatar_id=session.capsule_a.avatar_id,
                    content="",
                    is_final=False,
                )

                # Record turn in transcript
                session.add_turn(
                    session.capsule_a.avatar_id, full_a, topic_id, rnd, is_final
                )

                # --- Avatar B's turn (streaming) ---
                full_b = ""
                async for chunk in self.reasoner.debate_response_stream(
                    topic=topic["title"],
                    personality_context=self._personality_snapshot(session.capsule_b),
                    previous_turns=[t["content"] for t in session.transcript],
                ):
                    if not chunk:
                        continue
                    full_b += chunk
                    yield DebateTurn(
                        session_id=session.session_id,
                        topic_id=topic_id,
                        round=rnd,
                        speaker_avatar_id=session.capsule_b.avatar_id,
                        content=chunk,
                        is_final=is_final,
                    )

                # Signal that this avatar's turn is complete
                yield DebateTurn(
                    session_id=session.session_id,
                    topic_id=topic_id,
                    round=rnd,
                    speaker_avatar_id=session.capsule_b.avatar_id,
                    content="",
                    is_final=is_final,
                )

                # Record turn in transcript
                session.add_turn(
                    session.capsule_b.avatar_id, full_b, topic_id, rnd, is_final
                )

                if is_final:
                    break

        # Final turn with session closure signal
        yield DebateTurn(
            session_id=session.session_id,
            topic_id="",
            round=-1,
            speaker_avatar_id="",
            content="SESSION_COMPLETE",
            is_final=True,
        )

        logger.info(
            f"Streaming debate complete for session {session.session_id}: "
            f"{len(session.transcript)} turns"
        )

    def cleanup_stale_sessions(self, max_age_seconds: int = 3600):
        now = int(time.time())
        stale = [sid for sid, s in self._sessions.items() if now - s.created_at > max_age_seconds]
        for sid in stale:
            del self._sessions[sid]
        if stale:
            logger.info(f"Cleaned up {len(stale)} stale A2A sessions")
