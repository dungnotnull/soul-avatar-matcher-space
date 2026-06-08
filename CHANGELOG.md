# Changelog

All notable changes to soul-avatar-matcher will be documented in this file.

## [1.0.0] — 2026-06-08

### Added

**Phase 0 — Research & Environment Setup**
- Project directory structure (`src/`, `models/`, `data/`, `proto/`, `config/`, `scripts/`)
- `requirements.txt` with pinned versions for all dependencies
- `config/settings.py` with pydantic-settings schema
- `config/llm_settings.py` with provider selection and fallback chain
- `proto/avatar.proto` — AvatarCapsule, BigFiveScores, PersonalityVector, PendingMatch
- `proto/a2a_session.proto` — A2ADatingService with InitiateSession, StreamDebate, StreamFullDebate, SubmitMatchDecision
- Compiled protobuf stubs with gRPC service definitions
- SQLite v0 schema migration (`src/vault/schema.py`)

**Phase 1 — Core Personality Engine**
- `PersonalityExtractor` — Big Five (OCEAN) + 7-class emotion extraction from text
- `PersonalitySiameseEncoder` — Shared BERT backbone → 512-dim L2-normalized vector
- `ContrastiveLoss` + `TripletLoss` loss functions
- `SiamesePersonalityModel` — high-level wrapper for training and inference
- `OpenPsychometricsDataset` + `PersonalityPairDataset` — data loaders for Siamese training
- `SiameseTrainer` — training orchestration with AdamW, CosineAnnealing, early stopping
- `PersonalityUpdater` — nightly update loop with drift detection
- `AvatarCapsuleBuilder` — personality vector → protobuf capsule
- `PersonalityVaultManager` — SQLCipher AES-256 encrypted storage
- `DataIngestionClient` — sync REST client for folder 3/5 APIs

**Phase 2 — A2A Dating Runtime**
- `A2ASessionManager` — multi-round debate orchestrator with 10 structured topics
- `LocalSLMReasoner` — Ollama API wrapper with streaming and fallback
- `A2ADatingServicer` — synchronous gRPC server
- `AsyncA2ADatingServicer` — async gRPC server with parallel session handling
- `StreamFullDebate` RPC — real-time token-level streaming debate delivery
- `DynamicTopicSelector` — personality-profile-aware topic selection
- `CompatibilityScorer` — hybrid: cosine similarity + LLM judge + complementarity bonus
- `ConsentGate` — bilateral confirmation with match TTL and audit log
- `run_simulation` — N-session parallel benchmark tool

**Phase 3 — External LLM Integration**
- `ReportGenerator` — pluggable backend (Claude / GPT-4o / Ollama)
- Claude ephemeral prompt caching support
- Exponential backoff with 3 retries on all providers
- `LLMProvider` enum with fallback chain: Claude → GPT-4o → Ollama
- `validate_config()` system health check
- Provider-specific prompt templates

**Phase 4 — Self-Improving Knowledge Loop**
- `KnowledgeCrawler` — ArXiv XML API, Semantic Scholar REST API, HuggingFace Hub API
- `PaperSummarizer` — relevance scoring via domain embedding
- `KnowledgeBrainUpdater` — SECOND-KNOWLEDGE-BRAIN.md auto-updater with dedup
- `NotificationService` — console, file, and webhook notifications
- `weekly_knowledge_update.py` — full pipeline entry point for cron

**Phase 5 — Polish & Deployment**
- Streamlit web dashboard (Match Review, Profiles, Consent, Notifications, Health)
- FastAPI REST API backend (`src/api.py`)
- Docker + docker-compose (4 services: app, ollama, dashboard, cron-knowledge)
- 12 CLI commands via `python -m src`
- MIT License
- Security audit document (`SECURITY.md`)
- Full README with architecture diagram and quickstart
- `.env.example` with all configuration variables
- `.gitignore` for Python, Docker, data, and models
- `.editorconfig` for consistent code style
- `pyproject.toml` with full package metadata, scripts, dev dependencies
- `CONTRIBUTING.md` development guide
- `CODE_OF_CONDUCT.md`
- GitHub Actions CI/CD (`lint`, `import-check`, `docker-build`)
