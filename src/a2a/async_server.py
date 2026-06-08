"""
Async gRPC A2A server with parallel session handling and connection pooling.

Replaces the synchronous server with an asyncio-based implementation
that handles concurrent A2A sessions without blocking.
"""

from __future__ import annotations

import asyncio
import grpc.aio
from loguru import logger

from proto import a2a_session_pb2, a2a_session_pb2_grpc
from src.a2a.session_manager import A2ASessionManager
from src.a2a.slm_reasoner import LocalSLMReasoner
from src.matching.scorer import CompatibilityScorer
from src.consent.gate import ConsentGate
from config.settings import settings


class AsyncA2ADatingServicer(a2a_session_pb2_grpc.A2ADatingServiceServicer):
    def __init__(self):
        self.reasoner = LocalSLMReasoner()
        self.session_manager = A2ASessionManager(self.reasoner)
        self.scorer = CompatibilityScorer(self.reasoner)
        self.consent_gate = ConsentGate()
        self._active_sessions: dict[str, asyncio.Task] = {}
        self._session_semaphore = asyncio.Semaphore(50)

    async def InitiateSession(self, request, context):
        logger.info(f"InitiateSession request from {request.self_capsule.avatar_id}")
        try:
            session = self.session_manager.create_session(
                capsule_a=request.self_capsule,
                capsule_b=request.peer_capsule,
                topic_ids=list(request.topic_ids) if request.topic_ids else None,
                max_rounds=request.max_rounds_per_topic or 2,
            )

            async with self._session_semaphore:
                transcript = await asyncio.to_thread(
                    self.session_manager.run_debate, session
                )

            compatibility_score, score_breakdown = self.scorer.compute(
                session.capsule_a, session.capsule_b, transcript
            )

            if compatibility_score >= settings.COMPATIBILITY_THRESHOLD:
                match_id = self.consent_gate.initiate_match(
                    session.capsule_a, session.capsule_b, compatibility_score
                )
                return a2a_session_pb2.InitiateResponse(
                    session_id=session.session_id,
                    accepted=True,
                    message=f"Compatibility threshold met. Match ID: {match_id}. Awaiting consent.",
                )
            else:
                return a2a_session_pb2.InitiateResponse(
                    session_id=session.session_id,
                    accepted=False,
                    message=f"Compatibility score {compatibility_score:.2f} below threshold {settings.COMPATIBILITY_THRESHOLD}.",
                )
        except Exception as e:
            logger.error(f"InitiateSession failed: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
            return a2a_session_pb2.InitiateResponse(accepted=False, message=str(e))

    async def StreamDebate(self, request_iterator, context):
        async for request in request_iterator:
            session = self.session_manager.get_session(request.session_id)
            if session is None:
                yield a2a_session_pb2.DebateTurn(
                    session_id=request.session_id,
                    content="Session not found.",
                )
                return

            response = await asyncio.to_thread(
                self.reasoner.debate_response,
                topic=request.topic_id,
                personality_context=f"Responding in debate round {request.round}",
            )

            yield a2a_session_pb2.DebateTurn(
                session_id=request.session_id,
                topic_id=request.topic_id,
                round=request.round,
                speaker_avatar_id=session.capsule_b.avatar_id,
                content=response,
                is_final=request.is_final,
            )

    async def StreamFullDebate(self, request, context):
        """Run a full debate with real-time streaming of each avatar's response tokens.

        Client sends an InitiateRequest, server creates a session and streams back
        DebateTurn messages as the SLM generates response tokens. The final turn
        carries content='SESSION_COMPLETE' and is_final=True.
        """
        logger.info(f"StreamFullDebate request from {request.self_capsule.avatar_id}")
        try:
            session = self.session_manager.create_session(
                capsule_a=request.self_capsule,
                capsule_b=request.peer_capsule,
                topic_ids=list(request.topic_ids) if request.topic_ids else None,
                max_rounds=request.max_rounds_per_topic or 2,
            )

            async with self._session_semaphore:
                async for turn in self.session_manager.run_debate_stream(session):
                    yield turn

            transcript = session.transcript
            compatibility_score, score_breakdown = self.scorer.compute(
                session.capsule_a, session.capsule_b, transcript
            )

            logger.info(
                f"StreamFullDebate complete: session={session.session_id}, "
                f"score={compatibility_score:.4f}"
            )

            if compatibility_score >= settings.COMPATIBILITY_THRESHOLD:
                self.consent_gate.initiate_match(
                    session.capsule_a, session.capsule_b, compatibility_score
                )

        except Exception as e:
            logger.error(f"StreamFullDebate failed: {e}")
            yield a2a_session_pb2.DebateTurn(
                content=f"ERROR: {str(e)}",
                is_final=True,
            )

    async def SubmitMatchDecision(self, request, context):
        logger.info(f"MatchDecision: session={request.session_id}, avatar={request.avatar_id}, confirmed={request.confirmed}")
        try:
            result = self.consent_gate.process_decision(
                session_id=request.session_id,
                avatar_id=request.avatar_id,
                confirmed=request.confirmed,
            )
            return a2a_session_pb2.MatchResult(
                session_id=request.session_id,
                matched=result["matched"],
                message=result["message"],
                compatibility_score=result.get("compatibility_score", 0.0),
            )
        except Exception as e:
            logger.error(f"SubmitMatchDecision failed: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
            return a2a_session_pb2.MatchResult(matched=False, message=str(e))


class AsyncA2AServer:
    def __init__(self, host: str | None = None, max_workers: int | None = None):
        self.host = host or settings.GRPC_HOST
        self.max_workers = max_workers or settings.GRPC_MAX_WORKERS
        self._server: grpc.aio.Server | None = None
        self._servicer: AsyncA2ADatingServicer | None = None

    @property
    def servicer(self) -> AsyncA2ADatingServicer:
        if self._servicer is None:
            self._servicer = AsyncA2ADatingServicer()
        return self._servicer

    async def start(self):
        self._server = grpc.aio.server(
            options=[
                ("grpc.max_concurrent_streams", self.max_workers * 10),
                ("grpc.so_reuseport", 1),
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.http2.min_time_between_pings_ms", 10000),
                ("grpc.http2.max_pings_without_data", 0),
            ],
        )
        a2a_session_pb2_grpc.add_A2ADatingServiceServicer_to_server(
            self.servicer, self._server
        )
        self._server.add_insecure_port(self.host)
        await self._server.start()
        logger.info(f"Async A2A gRPC server started on {self.host} (max_workers={self.max_workers})")

    async def stop(self, grace: float = 5.0):
        if self._server:
            await self._server.stop(grace)
            self._server = None
            logger.info("A2A gRPC server stopped.")

    async def serve_forever(self):
        if self._server is None:
            await self.start()
        await self._server.wait_for_termination()


async def serve_async(host: str | None = None, max_workers: int | None = None):
    server = AsyncA2AServer(host=host, max_workers=max_workers)
    await server.start()
    return server
