"""
gRPC A2A server — accepts avatar capsules, spawns A2A debate sessions via gRPC.

Implements the A2ADatingService defined in a2a_session.proto.
"""

from __future__ import annotations

import grpc
from concurrent import futures
from loguru import logger

from proto import a2a_session_pb2, a2a_session_pb2_grpc
from proto.avatar_pb2 import AvatarCapsule
from src.a2a.session_manager import A2ASessionManager
from src.a2a.slm_reasoner import LocalSLMReasoner
from src.matching.scorer import CompatibilityScorer
from src.consent.gate import ConsentGate
from config.settings import settings


class A2ADatingServicer(a2a_session_pb2_grpc.A2ADatingServiceServicer):
    def __init__(self):
        self.reasoner = LocalSLMReasoner()
        self.session_manager = A2ASessionManager(self.reasoner)
        self.scorer = CompatibilityScorer(self.reasoner)
        self.consent_gate = ConsentGate()

    def InitiateSession(self, request, context):
        logger.info(f"InitiateSession request from {request.self_capsule.avatar_id}")
        try:
            session = self.session_manager.create_session(
                capsule_a=request.self_capsule,
                capsule_b=request.peer_capsule,
                topic_ids=list(request.topic_ids) if request.topic_ids else None,
                max_rounds=request.max_rounds_per_topic or 2,
            )

            transcript = self.session_manager.run_debate(session)

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
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return a2a_session_pb2.InitiateResponse(accepted=False, message=str(e))

    def StreamDebate(self, request_iterator, context):
        for request in request_iterator:
            session = self.session_manager.get_session(request.session_id)
            if session is None:
                yield a2a_session_pb2.DebateTurn(
                    session_id=request.session_id,
                    content="Session not found.",
                )
                return

            response = self.reasoner.debate_response(
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

    def SubmitMatchDecision(self, request, context):
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
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return a2a_session_pb2.MatchResult(matched=False, message=str(e))


def serve(host: str | None = None, max_workers: int | None = None):
    host = host or settings.GRPC_HOST
    max_workers = max_workers or settings.GRPC_MAX_WORKERS

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    a2a_session_pb2_grpc.add_A2ADatingServiceServicer_to_server(
        A2ADatingServicer(), server
    )
    server.add_insecure_port(host)
    server.start()
    logger.info(f"A2A gRPC server started on {host}")
    return server
