"""
CLI entry point for soul-avatar-matcher.

Commands:
    python -m src init           run first personality assessment
    python -m src update         run nightly personality update
    python -m src match          run A2A match between two avatars
    python -m src serve          start gRPC server
    python -m src serve-async    start async gRPC server
    python -m src status         check personality status
    python -m src knowledge      run knowledge base update
    python -m src simulate       run N simulated A2A sessions
    python -m src validate       validate config and check health
    python -m src dashboard      launch Streamlit dashboard
    python -m src train          train Siamese model
"""

from __future__ import annotations

import sys
import uuid
import asyncio
from loguru import logger

from config.settings import settings
from config.llm_settings import LLMProvider, resolve_provider, resolve_with_fallback


def cmd_init():
    """Run first personality assessment from text input."""
    from src.personality.extractor import PersonalityExtractor
    from src.personality.siamese_model import SiamesePersonalityModel
    from src.vault.manager import PersonalityVaultManager
    from src.ingestion.data_client import DataIngestionClient

    print("=== soul-avatar-matcher: Initial Personality Assessment ===\n")
    user_id = input("User ID (or press Enter for auto-generated): ").strip()
    if not user_id:
        user_id = str(uuid.uuid4())
        print(f"Auto-generated user ID: {user_id}")

    print("\nData source options:")
    print("  1. Fetch from folder 3 and folder 5 APIs")
    print("  2. Paste text samples manually")
    print("  3. Load from file")
    choice = input("Choice [1-3]: ").strip()

    client = DataIngestionClient()
    if choice == "1":
        texts = client.fetch_all(user_id)
    elif choice == "3":
        path = input("File path: ").strip()
        texts = DataIngestionClient.from_file(path)
    else:
        texts = DataIngestionClient.manual_input()

    if not texts:
        print("No text data provided. Aborting.")
        return

    print(f"\nProcessing {len(texts)} text samples...")

    extractor = PersonalityExtractor()
    bf_list, em_list = extractor.extract_batch(texts)
    avg_bf, avg_em = PersonalityExtractor.aggregate_profiles(bf_list, em_list)

    print("\n--- Big Five Profile ---")
    for trait, value in avg_bf.items():
        bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
        print(f"  {trait.capitalize():20s}: {bar} {value:.2f}")

    print("\n--- Emotion Baseline ---")
    for em, value in sorted(avg_em.items(), key=lambda x: x[1], reverse=True):
        print(f"  {em:12s}: {value:.3f}")

    encoder = SiamesePersonalityModel()
    combined = " ".join(texts)
    vector = encoder.encode_single(combined)

    vault = PersonalityVaultManager()
    vault.initialize()
    vault.store_vector(
        user_id=user_id,
        vector=vector,
        big_five=avg_bf,
        emotions=avg_em,
        fingerprint_hash="init",
        source_window_count=len(texts),
    )

    print(f"\n✓ Personality assessment complete! Vector stored in vault for user {user_id}")
    client.close()


def cmd_update():
    """Run nightly personality update."""
    from src.personality.updater import PersonalityUpdater
    from src.ingestion.data_client import DataIngestionClient

    user_id = input("User ID: ").strip()
    client = DataIngestionClient()
    texts = client.fetch_all(user_id)

    if not texts:
        print("No new data found. Loading from manual input fallback.")
        texts = DataIngestionClient.manual_input()
    if not texts:
        print("No data to process. Aborting.")
        return

    updater = PersonalityUpdater()
    summary = updater.update(user_id, texts)
    print(f"\n--- Update Summary ---")
    print(f"  Row ID: {summary['row_id']}")
    print(f"  Fingerprint: {summary['fingerprint'][:16]}...")
    print(f"  Drift Alert: {'⚠ YES' if summary['drift_alert'] else '✓ No'}")
    client.close()


def cmd_status():
    """Check personality status for a user."""
    from src.personality.updater import PersonalityUpdater

    user_id = input("User ID: ").strip()
    updater = PersonalityUpdater()
    status = updater.get_status(user_id)

    if status is None:
        print(f"No personality data found for user {user_id}.")
        return

    profile = status["profile"]
    print(f"\n--- Personality Status for {user_id} ---")
    print(f"  Last Updated: {profile['created_at']}")
    print(f"  Big Five: O={profile['big_five_o']:.2f} C={profile['big_five_c']:.2f} "
          f"E={profile['big_five_e']:.2f} A={profile['big_five_a']:.2f} N={profile['big_five_n']:.2f}")
    print(f"  Drift Delta: {profile['drift_delta']:.4f}")
    print(f"  Drift Alert: {'⚠ YES' if status['drift_alert'] else '✓ No'}")

    if status["drift_history"]:
        print(f"\n  Recent Drift History ({len(status['drift_history'])} entries):")
        for h in status["drift_history"][:3]:
            print(f"    {h['created_at']}: delta={h['drift_delta']:.4f}")


def cmd_match():
    """Run simulated A2A match between two user IDs."""
    from src.avatar.capsule_builder import AvatarCapsuleBuilder
    from src.personality.siamese_model import SiamesePersonalityModel
    from src.personality.extractor import PersonalityExtractor
    from src.vault.manager import PersonalityVaultManager
    from src.a2a.session_manager import A2ASessionManager
    from src.matching.scorer import CompatibilityScorer
    from src.consent.gate import ConsentGate

    vault = PersonalityVaultManager()

    user_a = input("User A ID: ").strip()
    profile_a = vault.get_latest_profile(user_a)
    if profile_a is None:
        print(f"No personality data for user {user_a}. Run 'init' first.")
        return

    user_b = input("User B ID: ").strip()
    profile_b = vault.get_latest_profile(user_b)
    if profile_b is None:
        print(f"No personality data for user {user_b}. Run 'init' first.")
        return

    encoder = SiamesePersonalityModel()
    builder = AvatarCapsuleBuilder(avatar_id=user_a)
    capsule_a = builder.build(
        vector=encoder.encode_single("placeholder"),
        big_five={"openness": profile_a["big_five_o"], "conscientiousness": profile_a["big_five_c"],
                  "extraversion": profile_a["big_five_e"], "agreeableness": profile_a["big_five_a"],
                  "neuroticism": profile_a["big_five_n"]},
        emotions={"joy": profile_a["emotion_joy"], "sadness": profile_a["emotion_sadness"],
                  "anger": profile_a["emotion_anger"], "fear": profile_a["emotion_fear"],
                  "surprise": profile_a["emotion_surprise"], "disgust": profile_a["emotion_disgust"],
                  "neutral": profile_a["emotion_neutral"]},
    )

    builder_b = AvatarCapsuleBuilder(avatar_id=user_b)
    capsule_b = builder_b.build(
        vector=encoder.encode_single("placeholder_b"),
        big_five={"openness": profile_b["big_five_o"], "conscientiousness": profile_b["big_five_c"],
                  "extraversion": profile_b["big_five_e"], "agreeableness": profile_b["big_five_a"],
                  "neuroticism": profile_b["big_five_n"]},
        emotions={"joy": profile_b["emotion_joy"], "sadness": profile_b["emotion_sadness"],
                  "anger": profile_b["emotion_anger"], "fear": profile_b["emotion_fear"],
                  "surprise": profile_b["emotion_surprise"], "disgust": profile_b["emotion_disgust"],
                  "neutral": profile_b["emotion_neutral"]},
    )

    print(f"\nRunning A2A compatibility debate between {user_a} and {user_b}...")
    manager = A2ASessionManager()
    session = manager.create_session(capsule_a, capsule_b)

    try:
        transcript = manager.run_debate(session)
    except Exception as e:
        logger.warning(f"SLM debate failed (Ollama may be offline): {e}")
        print("SLM unavailable — running scoring on personality vectors only.")
        transcript = []

    scorer = CompatibilityScorer()
    score, breakdown = scorer.compute(capsule_a, capsule_b, transcript)

    print(f"\n--- Compatibility Score ---")
    print(f"  Composite:        {breakdown['composite_score']:.4f}")
    print(f"  Vector Similarity: {breakdown['vector_similarity']:.4f}")
    print(f"  Dialogue Coherence:{breakdown['dialogue_coherence']:.4f}")
    print(f"  Complementarity:   {breakdown['complementarity_bonus']:.4f}")

    if score >= settings.COMPATIBILITY_THRESHOLD:
        print(f"\n✓ Threshold met ({score:.2%} ≥ {settings.COMPATIBILITY_THRESHOLD:.0%})!")
        consent = ConsentGate()
        match_id = consent.initiate_match(capsule_a, capsule_b, score)
        print(f"  Match ID: {match_id}")
        print(f"  Report generated. Both users must confirm to reveal contact.")

        report = consent.get_anonymized_report(match_id, user_a)
        print(f"\n--- Anonymized Report (for {user_a}) ---")
        print(report[:500])

        confirm = input(f"\n{user_a}, confirm match? (y/n): ").strip().lower()
        result = consent.process_decision(match_id, user_a, confirm == "y")
        print(f"  → {result['message']}")

        if not result["matched"]:
            confirm_b = input(f"\n{user_b}, confirm match? (y/n): ").strip().lower()
            result_b = consent.process_decision(match_id, user_b, confirm_b == "y")
            print(f"  → {result_b['message']}")
    else:
        print(f"\n✗ Below threshold ({score:.2%} < {settings.COMPATIBILITY_THRESHOLD:.0%}). No match.")


def cmd_serve():
    """Start gRPC A2A server."""
    from src.a2a.server import serve
    print(f"Starting A2A gRPC server on {settings.GRPC_HOST}...")
    server = serve()
    server.wait_for_termination()


def cmd_serve_async():
    """Start async gRPC A2A server with parallel session handling."""
    from src.a2a.async_server import AsyncA2AServer
    async def _run():
        server = AsyncA2AServer()
        await server.start()
        print(f"Async A2A gRPC server started on {settings.GRPC_HOST}")
        await server.serve_forever()
    asyncio.run(_run())


def cmd_knowledge():
    """Run knowledge base update."""
    from scripts.weekly_knowledge_update import main as wk_main
    wk_main()


def cmd_dashboard():
    """Launch Streamlit web dashboard."""
    import subprocess
    import os
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
    subprocess.run(["streamlit", "run", dashboard_path])


def cmd_api():
    """Start FastAPI REST server."""
    import subprocess
    api_path = os.path.join(os.path.dirname(__file__), "api.py")
    subprocess.run(["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"])


def cmd_simulate():
    """Run N simulated A2A sessions for benchmarking."""
    from src.a2a.simulate import run_simulation
    count = 10
    parallel = False
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] in ("--count", "-c") and i + 1 < len(args):
            count = int(args[i + 1])
            i += 2
        elif args[i] in ("--parallel", "-p"):
            parallel = True
            i += 1
        else:
            i += 1
    run_simulation(count=count, parallel=parallel)


def cmd_validate():
    """Validate config and check system health."""
    from src.reports.generator import validate_config
    from src.a2a.slm_reasoner import LocalSLMReasoner
    print("=== System Validation ===\n")
    print(f"Config root: {settings.PROJECT_ROOT}")
    print(f"DB path: {settings.db_path_absolute}")
    print(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"gRPC host: {settings.GRPC_HOST}")
    print(f"Compatibility threshold: {settings.COMPATIBILITY_THRESHOLD}")
    print()
    print("LLM provider check:")
    try:
        from config.llm_settings import get_available_providers
        providers = get_available_providers()
        print(f"  Available: {[p.value for p in providers]}")
        provider = resolve_with_fallback()
        print(f"  Active: {provider.value}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    reasoner = LocalSLMReasoner()
    ollama_ok = reasoner.health_check()
    print(f"Ollama health: {'✓ reachable' if ollama_ok else '✗ unreachable'}")
    print()
    config = validate_config()
    for k, v in config.items():
        status = "✓" if v is True else f"✗ ({v})"
        print(f"  {k}: {status}")


def cmd_train():
    """Train Siamese personality model (dry-run check)."""
    print("=== Siamese Model Training Setup ===\n")
    from src.personality.trainer import train_siamese_model
    from src.personality.siamese_model import PersonalitySiameseEncoder
    encoder = PersonalitySiameseEncoder()
    total_params = sum(p.numel() for p in encoder.parameters())
    trainable_params = sum(p.numel() for p in encoder.parameters() if p.requires_grad)
    print(f"Encoder backbone: {encoder.backbone_name}")
    print(f"Projection dim: {encoder.projection_dim}")
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print()
    resp = input("Start training? This will download the dataset and train for 10 epochs. (y/n): ").strip().lower()
    if resp == "y":
        metrics = train_siamese_model(epochs=10, batch_size=32, device="cpu")
        print(f"\nTraining complete: {metrics}")


def print_usage():
    print("Usage: python -m src <command> [options]")
    print()
    print("Commands:")
    print("  init              Run first personality assessment")
    print("  update            Run nightly personality update")
    print("  match             Run A2A compatibility debate between two users")
    print("  serve             Start synchronous gRPC A2A server")
    print("  serve-async       Start async gRPC server (parallel sessions)")
    print("  status            Check personality status for a user")
    print("  knowledge         Run knowledge base crawler and update")
    print("  simulate [opts]   Run N simulated A2A sessions (--count N --parallel)")
    print("  validate          Validate config and check system health")
    print("  dashboard         Launch Streamlit web dashboard")
    print("  api               Start FastAPI REST server")
    print("  train             Train Siamese personality model")


def main():
    logger.remove()
    logger.add(sys.stderr, level=settings.LOG_LEVEL)

    if len(sys.argv) < 2:
        print_usage()
        return

    cmd = sys.argv[1].lower()
    if cmd == "init":
        cmd_init()
    elif cmd == "update":
        cmd_update()
    elif cmd == "match":
        cmd_match()
    elif cmd == "serve":
        cmd_serve()
    elif cmd == "serve-async":
        cmd_serve_async()
    elif cmd == "status":
        cmd_status()
    elif cmd == "knowledge":
        cmd_knowledge()
    elif cmd == "simulate":
        cmd_simulate()
    elif cmd == "validate":
        cmd_validate()
    elif cmd == "dashboard":
        cmd_dashboard()
    elif cmd == "api":
        cmd_api()
    elif cmd == "train":
        cmd_train()
    else:
        print(f"Unknown command: {cmd}")
        print_usage()


if __name__ == "__main__":
    main()
