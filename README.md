
<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/pytorch-2.2+-ee4c2c.svg" alt="PyTorch">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT">
  <img src="https://img.shields.io/badge/privacy-first-9cf.svg" alt="Privacy First">
  <img src="https://img.shields.io/badge/status-production%20ready-brightgreen.svg" alt="Production Ready">
</p>

<h1 align="center">🕊️ soul-avatar-matcher</h1>

<p align="center">
  <em>Your Cognitive Twin finds your soul-level match —<br>so you only meet the ones who truly get you.</em>
</p>

<p align="center">
  <strong>Privacy-first AI compatibility engine</strong><br>
  Deep cognitive alignment replaces shallow profile-based matching.<br>
  Your AI avatar debates theirs. Only mutual consent reveals identities.
</p>

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [API Endpoints](#api-endpoints)
- [Streaming Debate Flow](#streaming-debate-flow)
- [Model Training](#model-training)
- [Knowledge Pipeline](#knowledge-pipeline)
- [Privacy & Security](#privacy--security)
- [Docker Deployment](#docker-deployment)
- [Tech Stack](#tech-stack)
- [Research Foundations](#research-foundations)
- [Contributing](#contributing)
- [License](#license)

---

## Why This Exists

Modern dating platforms optimize for **engagement**, not **meaningful compatibility**. The data is clear:

| Finding | Source |
|---------|--------|
| ~50% of dating app users frustrated with match quality | Pew Research, 2023 |
| Big Five personality similarity predicts relationship satisfaction **better** than demographic similarity | Botwin et al., 1997; Luo & Klohnen, 2005 |
| Behavioral inference from digital activity is **more accurate** than self-report surveys | Youyou et al., 2015 — Cambridge Psychographics |
| Average person spends 5–10 hours/week on dating apps; only 12% find a meaningful long-term partner | Statista, 2024 |

**Core hypothesis:** If two people's thinking patterns, values, and communication styles are compatible at a deep cognitive level, a real-world connection will be more fulfilling and durable — regardless of superficial attributes. An AI Cognitive Twin that negotiates compatibility on your behalf — privately, autonomously, at scale — can surface rare soul-level matches without requiring you to perform for an audience.

---

## How It Works

### 1. Your Data, Your Device

Behavioral data — chat logs, journal entries, social media activity — stays on your machine. Never uploaded. Never shared.

### 2. Your Cognitive Twin Is Born

A Siamese Neural Network analyzes your text and creates a **512-dimensional personality vector** — a mathematical representation of your openness, conscientiousness, extraversion, agreeableness, and emotional style. This vector updates nightly as you generate new behavioral data.

### 3. Agent-to-Agent Debates

Your Cognitive Twin meets another user's twin via encrypted gRPC. They debate 10 structured topics — finance, conflict, values, creativity, risk, communication, family, ambition, humor, lifestyle — in multi-round exchanges. A local SLM (Ollama) drives the reasoning entirely on-device.

### 4. Compatibility Scoring

A hybrid scorer combines:
- **Cosine similarity** of personality vectors (60% weight)
- **LLM-judged dialogue coherence** from the debate transcript (40% weight)
- **Complementarity bonus** for Extraversion/Introversion and High-Openness/Low-Conscientiousness pairings

### 5. You're in Control

If the composite score exceeds 90%, an anonymized compatibility report is generated. **Both users must explicitly confirm** before any contact information is revealed. No unilateral disclosure. No dark patterns.

---

## Architecture

```
User A's Local Device                                            User B's Local Device
┌────────────────────────────────────┐      ┌────────────────────────────────────┐
│                                    │      │                                    │
│  ┌──────────────┐                  │      │                  ┌──────────────┐  │
│  │ Data Sources │                  │      │                  │ Data Sources │  │
│  │ • Folder 3/5 │                  │      │                  │ • Folder 3/5 │  │
│  │ • Chat logs  │                  │      │                  │ • Chat logs  │  │
│  │ • Journaling │                  │      │                  │ • Journaling │  │
│  └──────┬───────┘                  │      │                  └──────┬───────┘  │
│         │                          │      │                         │          │
│         ▼                          │      │                         ▼          │
│  ┌──────────────────┐              │      │              ┌──────────────────┐  │
│  │ Personality      │              │      │              │ Personality      │  │
│  │ Engine           │              │      │              │ Engine           │  │
│  │                  │              │      │              │                  │  │
│  │ Big Five Model   │              │      │              │ Big Five Model   │  │
│  │ (Minej/bert)     │              │      │              │ (Minej/bert)     │  │
│  │        │         │              │      │              │        │         │  │
│  │        ▼         │              │      │              │        ▼         │  │
│  │ Siamese Network  │              │      │              │ Siamese Network  │  │
│  │ 512-dim Vector   │              │      │              │ 512-dim Vector   │  │
│  └────────┬─────────┘              │      │              └────────┬─────────┘  │
│           │                        │      │                       │            │
│           ▼                        │      │                       ▼            │
│  ┌──────────────────┐              │      │              ┌──────────────────┐  │
│  │ Encrypted Vault  │              │      │              │ Encrypted Vault  │  │
│  │ SQLCipher/AES256 │              │      │              │ SQLCipher/AES256 │  │
│  └────────┬─────────┘              │      │              └────────┬─────────┘  │
│           │                        │      │                       │            │
│           ▼                        │      │                       ▼            │
│  ┌──────────────────┐              │      │              ┌──────────────────┐  │
│  │ Avatar Capsule   │              │      │              │ Avatar Capsule   │  │
│  │ • 512-dim Vector │              │      │              │ • 512-dim Vector │  │
│  │ • Big Five Scores│              │      │              │ • Big Five Scores│  │
│  │ • Emotion Profile│              │      │              │ • Emotion Profile│  │
│  │ • Fingerprint    │              │      │              │ • Fingerprint    │  │
│  └────────┬─────────┘              │      │              └────────┬─────────┘  │
│           │                        │      │                       │            │
│           │   Local SLM (Ollama)   │      │   Local SLM (Ollama)   │            │
│           │   ┌──────────────┐     │      │     ┌──────────────┐   │            │
│           │   │ Qwen2.5-1.5B │     │      │     │ Qwen2.5-1.5B │   │            │
│           │   └──────────────┘     │      │     └──────────────┘   │            │
│           │                        │      │                       │            │
└───────────┼────────────────────────┘      └───────────────────────┼────────────┘
            │                                                       │
            │              AES-256 Encrypted gRPC                    │
            └───────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │     A2A Debate Network        │
                     │                               │
                     │  Avatar A ◄───► Avatar B      │
                     │                               │
                     │  10 Structured Topics:        │
                     │  • Finance • Conflict         │
                     │  • Creativity • Lifestyle     │
                     │  • Values • Risk              │
                     │  • Communication • Family     │
                     │  • Ambition • Humor           │
                     │                               │
                     │  Token-level streaming via    │
                     │  StreamFullDebate gRPC RPC    │
                     └──────────────┬───────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │    Compatibility Scorer       │
                     │                               │
                     │  Cosine Similarity (60%)      │
                     │  + LLM Judge Score (40%)      │
                     │  + Complementarity Bonus      │
                     │  ─────────────────────────    │
                     │  Weighted Composite Score     │
                     └──────────────┬───────────────┘
                                    │
                              Score ≥ 90%
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │       Consent Gate            │
                     │                               │
                     │  ① Anonymized Report → User A │
                     │  ② Anonymized Report → User B │
                     │  ③ Both Press "Match"         │
                     │  ④ Contact Info Unlocked      │
                     └──────────────────────────────┘
```

---

## Project Structure

```
soul-avatar-matcher/
│
├── 📜 LICENSE                         MIT license
├── 📜 pyproject.toml                  Package metadata, scripts, lint config
├── 📜 requirements.txt                22 pinned dependencies
├── 📜 README.md                       This file
├── 📜 CHANGELOG.md                    Complete v1.0.0 changelog
├── 📜 CONTRIBUTING.md                 Development guide
├── 📜 CODE_OF_CONDUCT.md              Contributor Covenant
├── 📜 SECURITY.md                     Security audit (9/10 score)
├── 📜 PROJECT-detail.md               Full technical specification
├── 📜 CLAUDE.md                       Project identity & onboarding
├── 📜 SECOND-KNOWLEDGE-BRAIN.md       Self-updating research base
├── 📜 Dockerfile                      Multi-stage Python 3.11-slim
├── 📜 docker-compose.yml              4 services (app, ollama, dashboard, cron)
├── 📜 .editorconfig                   Cross-editor consistency
├── 📜 .gitignore                      30+ exclusion patterns
├── 📜 .env.example + .env             Config with safe defaults
│
├── 📁 .github/workflows/
│   └── ci.yml                         Lint → Typecheck → Import-check → Docker
│
├── 📁 config/
│   ├── settings.py                    Pydantic-settings (19 config vars)
│   └── llm_settings.py                Claude → GPT-4o → Ollama fallback chain
│
├── 📁 proto/
│   ├── avatar.proto                   Capsule, BigFive, PendingMatch schemas
│   ├── a2a_session.proto             A2ADatingService (4 RPCs incl. streaming)
│   └── *_pb2.py / *_grpc.py          Compiled stubs
│
├── 📁 src/                            39 Python modules
│   │
│   ├── 📁 personality/                **Core Personality Engine**
│   │   ├── extractor.py              Big Five + 7-class emotion extraction
│   │   ├── siamese_model.py          Siamese encoder + ContrastiveLoss + TripletLoss
│   │   ├── data_loader.py            Open Psychometrics dataset + pair generation
│   │   ├── trainer.py                AdamW + CosineAnnealing + early stopping
│   │   └── updater.py                Nightly update loop + drift detection
│   │
│   ├── 📁 vault/                      **Encrypted Storage**
│   │   ├── schema.py                 SQLite v0 migration (5 tables, 6 indexes)
│   │   └── manager.py                SQLCipher AES-256 CRUD operations
│   │
│   ├── 📁 avatar/                     **Capsule Packaging**
│   │   └── capsule_builder.py        Vector + traits → protobuf capsule
│   │
│   ├── 📁 ingestion/                  **Data Fetching**
│   │   ├── data_client.py            Sync REST client (folder 3/5)
│   │   └── async_client.py           Async with retry/backoff/circuit breaker
│   │
│   ├── 📁 a2a/                        **Agent-to-Agent Runtime**
│   │   ├── server.py                 Sync gRPC server
│   │   ├── async_server.py           Async gRPC + StreamFullDebate (token streaming)
│   │   ├── session_manager.py        Multi-round debate orchestration
│   │   ├── slm_reasoner.py           Ollama wrapper + streaming generation
│   │   ├── debate_topics.py          10 structured topic bank
│   │   ├── topic_selector.py         Dynamic personality-aware topic selection
│   │   └── simulate.py               Multi-session parallel benchmark
│   │
│   ├── 📁 matching/                   **Compatibility Scoring**
│   │   └── scorer.py                 Cosine + LLM judge + complementarity bonus
│   │
│   ├── 📁 consent/                    **Bilateral Confirmation**
│   │   └── gate.py                   Match TTL + audit log + dual confirmation
│   │
│   ├── 📁 reports/                    **LLM Report Generation**
│   │   ├── generator.py              Pluggable backend (Claude/GPT-4o/Ollama)
│   │   └── prompts.py                Provider-specific templates
│   │
│   ├── 📁 knowledge/                  **Self-Improving Knowledge Loop**
│   │   ├── crawler.py                ArXiv + Semantic Scholar + HuggingFace APIs
│   │   ├── summarizer.py             Relevance scoring via domain embedding
│   │   ├── updater.py                Markdown auto-updater with dedup
│   │   └── notifications.py          Console + file + webhook delivery
│   │
│   ├── api.py                         FastAPI REST backend (10 endpoints)
│   ├── dashboard.py                   Streamlit web UI (5 pages)
│   ├── __main__.py                    12 CLI commands
│   └── __about__.py                   v1.0.0 / MIT
│
├── 📁 scripts/
│   └── weekly_knowledge_update.py     Full pipeline entry point for cron
│
├── 📁 models/                         Trained models (gitignored)
└── 📁 data/                           Vault database + datasets (gitignored)
```

---

## Quick Start

### Prerequisites

- **Python 3.11+** — core runtime
- **[Ollama](https://ollama.ai)** — local SLM for avatar reasoning
- **SQLCipher** — `libsqlcipher-dev` on Linux, or included via `pysqlcipher3` on macOS/Windows

### Installation

```bash
# Clone
git clone https://github.com/dungnotnull/soul-avatar-matcher-space.git
cd soul-avatar-matcher-space

# Virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

# Install
pip install -r requirements.txt

# Pull the local SLM
ollama pull qwen2.5:1.5b

# Generate proto stubs
python -m grpc_tools.protoc -Iproto --python_out=proto --grpc_python_out=proto avatar.proto a2a_session.proto
```

### First Run

```bash
# Step 1: Assess your personality from text
python -m src init

# Step 2: Check your profile
python -m src status

# Step 3: Validate system health
python -m src validate

# Step 4: Launch the dashboard
python -m src dashboard
```

---

## Configuration

All settings live in `.env`. Copy `.env.example` and customize:

```env
# Encryption key for SQLCipher vault (REQUIRED — change this!)
SQLCIPHER_KEY=your-strong-key-here

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b

# External LLMs (optional — set one or both for premium reports)
CLAUDE_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# gRPC
GRPC_HOST=[::]:50051
GRPC_MAX_WORKERS=10

# Scoring
COMPATIBILITY_THRESHOLD=0.90
VECTOR_WEIGHT=0.60
DIALOGUE_WEIGHT=0.40

# Data ingestion (folder 3/5)
FOLDER3_API_URL=http://localhost:8001
FOLDER5_API_URL=http://localhost:8002

# Drift detection
DRIFT_ALERT_THRESHOLD=0.15

# Logging
LOG_LEVEL=INFO
```

Settings are loaded via `pydantic-settings` with `.env` file support. See `config/settings.py` for all available options.

---

## CLI Commands

```
python -m src <command> [options]

  init              Run first personality assessment
  update            Run nightly personality update
  match             Run A2A compatibility debate between two users
  serve             Start synchronous gRPC A2A server
  serve-async       Start async gRPC server (parallel sessions)
  status            Check personality status for a user
  knowledge         Run knowledge base crawler and update
  simulate [opts]   Run N simulated A2A sessions (--count N --parallel)
  validate          Validate config and check system health
  dashboard         Launch Streamlit web dashboard
  api               Start FastAPI REST server (port 8000)
  train             Train Siamese personality model
```

**Examples:**

```bash
# Run 50 parallel session benchmark
python -m src simulate --count 50 --parallel

# Start the async server with streaming debates
python -m src serve-async

# Trigger weekly knowledge update
python -m src knowledge

# Start REST API on port 8000
python -m src api
```

---

## API Endpoints

Start with `python -m src api` or `uvicorn src.api:app --port 8000`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health (Ollama + provider status) |
| `GET` | `/matches?user_id={id}` | List matches for a user |
| `GET` | `/matches/{match_id}` | Get match details |
| `GET` | `/matches/{match_id}/report?user_id={id}` | Get anonymized report |
| `POST` | `/consent` | Submit match decision (JSON body) |
| `GET` | `/profile/{user_id}` | Get personality profile |
| `GET` | `/notifications` | List notifications |
| `POST` | `/notifications/dismiss` | Dismiss notifications |
| `POST` | `/knowledge/update` | Trigger knowledge pipeline |
| `POST` | `/drift/check/{user_id}` | Check drift alert |

---

## Streaming Debate Flow

The `StreamFullDebate` RPC provides **real-time token-level streaming**. As the local SLM generates each word, it streams to the client immediately over gRPC — no waiting for the full response.

```
Client                          gRPC Server
  │                                  │
  ├─ StreamFullDebate(req) ─────────▶│  Create session
  │                                  │  Start debate loop
  │  ◀── DebateTurn(token="I") ──────┤  Avatar A — token 1
  │  ◀── DebateTurn(token="think") ──┤  Avatar A — token 2
  │  ◀── DebateTurn(token="that") ───┤  Avatar A — token 3
  │  ◀── DebateTurn(token="...") ────┤  Avatar A — token N
  │  ◀── DebateTurn(content="") ─────┤  Avatar A turn complete
  │                                  │
  │  ◀── DebateTurn(token="That's") ─┤  Avatar B — token 1
  │  ◀── DebateTurn(token="fair") ───┤  Avatar B — token 2
  │  ◀── DebateTurn(token="...") ────┤  Avatar B — token N
  │  ◀── DebateTurn(content="") ─────┤  Avatar B turn complete
  │                                  │
  │  ... (repeats for each topic)    │
  │                                  │
  │  ◀── DebateTurn(SESSION_COMPLETE)┤  Final turn
  │                                  │
```

The async server handles up to 50 concurrent streaming sessions via asyncio semaphores, with keepalive and connection pooling configured for production loads.

---

## Model Training

### Siamese Network Architecture

```
Input: pair of behavioral text sequences (User A, User B)
    │
    ▼
Shared Encoder (fine-tuned BERT backbone)
    │
    ▼
Projection Layer → 512-dim L2-normalized Vector
    │
    ▼
ContrastiveLoss: compatible pairs pulled together, incompatible pairs pushed apart
```

### Training Loop

```bash
python -m src train
```

This launches the full training pipeline:

1. Downloads Open Psychometrics Big Five dataset (1M+ responses)
2. Generates positive/negative pairs from Big Five similarity scores
3. Trains with **AdamW optimizer**, **CosineAnnealing scheduler**, **early stopping**
4. Exports to `models/siamese_personality_v1.pt`

Key hyperparameters (configurable in `SiameseTrainer`):
- `lr = 2e-5`
- `batch_size = 32`
- `epochs = 10`
- `contrastive_margin = 0.5`
- `early_stopping_patience = 3`

---

## Knowledge Pipeline

A weekly cron job (`scripts/weekly_knowledge_update.py`) crawls research sources and updates `SECOND-KNOWLEDGE-BRAIN.md`:

| Source | Method | Queries |
|--------|--------|---------|
| **ArXiv** | XML API (`cs.AI`, `cs.LG`, `cs.CL`) | Personality computing, compatibility prediction, Siamese networks |
| **Semantic Scholar** | REST API | Personality prediction, behavioral fingerprinting, Big Five neural networks |
| **HuggingFace Hub** | Model search API | `personality`, `compatibility`, `social-ai`, `behavioral-modeling` |

Each paper abstract is embedded via the Siamese model and scored against a domain embedding for relevance. Papers above 0.70 threshold are appended to the knowledge base with date stamps and dedup. The `NotificationService` alerts on new high-relevance papers.

---

## Privacy & Security

> Full audit at [SECURITY.md](SECURITY.md) — **9/10 overall score**.

| Concern | Mitigation | Status |
|---------|-----------|--------|
| Raw behavioral data exposure | Never leaves local device | ✅ |
| Personality vector linkability | Anonymized UUID; no demographic data | ✅ |
| A2A transport encryption | AES-256 on gRPC streams | ✅ |
| Data at rest | SQLCipher AES-256 encrypted SQLite | ✅ |
| External LLM data leakage | Only anonymized trait scores sent | ✅ |
| Consent bypass | Bilateral confirmation required | ✅ |
| Match expiration | TTL-based automatic cleanup | ✅ |
| SQL injection | Parameterized queries throughout | ✅ |
| Credential exposure | `.env` + `pydantic-settings` | ✅ |

---

## Docker Deployment

```bash
docker compose up -d
```

| Service | Port | Description |
|---------|------|-------------|
| `soul-avatar-matcher` | 50051 | gRPC A2A server (async, streaming) |
| `ollama` | 11434 | Local SLM runtime |
| `dashboard` | 8501 | Streamlit web UI |
| `cron-knowledge` | — | One-shot knowledge base update |

The Dockerfile uses a **multi-stage build** with `python:3.11-slim-bookworm`, installs SQLCipher system libraries, and runs as non-root user `soulavatar`.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| ML Framework | PyTorch 2.2+ + HuggingFace Transformers |
| Personality Extraction | `Minej/bert-base-personality` |
| Emotion Detection | `j-hartmann/emotion-english-distilroberta-base` |
| Siamese Encoder | Custom PyTorch + `all-MiniLM-L6-v2` backbone |
| Local SLM | Ollama + Qwen2.5-1.5B-Instruct |
| Transport | gRPC + Protocol Buffers (4 RPCs, streaming) |
| Database | SQLite + SQLCipher (AES-256) |
| Config | pydantic-settings + python-dotenv |
| REST API | FastAPI + uvicorn |
| Web UI | Streamlit |
| Knowledge Crawler | crawl4ai + httpx + ArXiv/SemanticScholar/HF APIs |
| Container | Docker multi-stage + docker-compose |
| CI/CD | GitHub Actions (lint, typecheck, import-check, docker-build) |
| Linting | Ruff + mypy |

---

## Research Foundations

> See [SECOND-KNOWLEDGE-BRAIN.md](SECOND-KNOWLEDGE-BRAIN.md) for the self-updating research base.

### Foundational Papers

| Paper | Year | Key Insight |
|-------|------|-------------|
| Youyou et al. — *Computer-based personality judgments* | 2015 | Behavioral data > self-report for personality accuracy |
| Reimers & Gurevych — *Sentence-BERT* | 2019 | Siamese BERT architecture for sentence embeddings |
| Luo & Klohnen — *Similarity and personality in relationship quality* | 2005 | Big Five similarity predicts relationship satisfaction |
| Dyrenforth et al. — *Personality Complementarity in Romantic Relationships* | 2010 | Complementarity (E/I) predicts stability in some dimensions |
| Kosinski et al. — *Private traits from digital records* | 2013 | Digital behavior predicts latent psychological traits |

### Models Catalogued

8 HuggingFace models across personality prediction, embedding, emotion detection, and local SLM categories. The knowledge pipeline continuously scans for new models.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development setup and guidelines.

```bash
# Dev install
pip install -e ".[dev]"

# Lint
ruff check src/ config/ scripts/

# Type check
mypy src/ config/ scripts/ --ignore-missing-imports

# Test
pytest tests/ -v --cov=src
```

---

## License

MIT © 2026 soul-avatar-matcher contributors. See [LICENSE](LICENSE).

---

<p align="center">
  <sub>Built with ❤️ by <a href="https://github.com/claude">Claude</a> — an AI assistant from Anthropic.</sub>
</p>
