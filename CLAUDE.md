# CLAUDE.md — soul-avatar-matcher

## Project Identity
**Name:** soul-avatar-matcher
**Tagline:** "Your Cognitive Twin finds your soul-level match — so you only meet the ones who truly get you."
**Status:** Phase 0 — Research & Environment Setup
**Folder:** `D:\Dungchan\6\`

---

## Core Problem Being Solved
Traditional dating platforms match people on photos, age, and superficial interests — yielding shallow connections with high churn. This project builds a **Cognitive Twin**: a privacy-first AI avatar that continuously learns a user's thinking patterns, values, communication style, and worldview from their daily digital behavior. The twin then autonomously runs thousands of Agent-to-Agent (A2A) "conversations" with other users' twins, scoring deep cognitive and emotional compatibility — before any real human interaction occurs. Only when two twins exceed a configurable compatibility threshold does the system surface an anonymized match report for mutual human approval.

---

## Architecture Summary
| Layer | Description |
|-------|-------------|
| **Data Ingestion** | Pulls behavioral data from omni-presence-soulmate (folder 5) and omni-second-brain-agent (folder 3) via local API |
| **Personality Engine** | Siamese Neural Network encodes user traits into a 512-dim Personality Vector; updated nightly |
| **A2A Dating Runtime** | gRPC-based peer protocol; encrypted avatar capsules exchange structured debate topics |
| **Compatibility Scorer** | Hybrid: cosine distance on personality vectors + LLM-judged dialogue analysis |
| **Consent Gate** | Human-in-the-loop approval at >90% compatibility; both parties must confirm before contact reveal |
| **Local SLM** | Drives avatar reasoning during A2A conversations; raw user data never leaves device |
| **Privacy Vault** | AES-256 encrypted local SQLite for all behavioral data; only anonymized vectors shared externally |

**ML Stack:** PyTorch (Siamese NN), sentence-transformers, scikit-learn (Big Five trait prediction), Ollama (local SLM)
**Local SLM:** Qwen2.5-1.5B-Instruct or Phi-3-mini via Ollama
**Optional External APIs:** Claude API, GPT-4o (used only for high-quality compatibility report generation; all raw data stays local)

---

## Key Technical Decisions
1. **Personality Vector Embedding** — Siamese Network trained on Big Five + MBTI labeled conversation datasets; cosine similarity is the primary compatibility metric
2. **A2A Protocol** — Avatar capsules transmitted via encrypted gRPC streams; capsule contains only the personality vector + anonymized behavioral fingerprint, never raw text
3. **Local-first SLM reasoning** — Avatar dialogue during A2A sessions runs entirely on-device via Ollama; no conversation transcript leaves the user's machine
4. **Incremental learning** — Personality matrix updated nightly via a lightweight online learning loop (no full retraining); drift detection triggers retraining if vector shift > threshold
5. **Graduated consent** — System displays anonymized compatibility report first; contact details revealed only after bilateral "Match" confirmation
6. **Data dependencies** — Ingests structured behavioral data from folder 3 (knowledge graph) and folder 5 (real-time presence data); fallback to manual onboarding quiz if those agents are offline

---

## External LLM API Integrations
| Provider | Purpose | Config Key |
|----------|---------|------------|
| Claude API (claude-sonnet-4-6) | Generate rich compatibility narrative reports | `CLAUDE_API_KEY` |
| GPT-4o | Alternative report generator (fallback) | `OPENAI_API_KEY` |
| Ollama (local) | Avatar A2A reasoning, always-on, primary | `OLLAMA_BASE_URL` (default: `http://localhost:11434`) |

---

## HuggingFace Models In Use
| Model ID | Purpose | Link |
|----------|---------|------|
| `Minej/bert-base-personality` | Big Five trait prediction from text | https://huggingface.co/Minej/bert-base-personality |
| `sentence-transformers/all-MiniLM-L6-v2` | Fast sentence embedding for personality vector base | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 |
| `BAAI/bge-large-en-v1.5` | High-quality embedding for compatibility vector space | https://huggingface.co/BAAI/bge-large-en-v1.5 |
| `j-hartmann/emotion-english-distilroberta-base` | Emotion detection from chat/writing samples | https://huggingface.co/j-hartmann/emotion-english-distilroberta-base |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | Sentiment polarity from behavioral text streams | https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest |
| `microsoft/phi-3-mini-4k-instruct` | Local SLM fallback if Qwen unavailable | https://huggingface.co/microsoft/phi-3-mini-4k-instruct |

---

## Current Active Development Tasks
- [ ] Set up Python virtual environment and install core dependencies
- [ ] Design SQLite schema for personality matrix storage
- [ ] Implement Big Five trait extractor using `Minej/bert-base-personality`
- [ ] Build Siamese Network architecture in PyTorch
- [ ] Define Avatar Capsule data schema (protobuf)
- [ ] Implement local gRPC server for A2A session handling
- [ ] Build nightly personality matrix update loop
- [ ] Create compatibility scorer (vector cosine + LLM judge)
- [ ] Build consent gate UI (CLI + optional web dashboard)
- [ ] Integrate crawl4ai self-update pipeline for SECOND-KNOWLEDGE-BRAIN

---

## Related Files
- `PROJECT-detail.md` — full technical specification and feature list
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` — phase-by-phase roadmap with milestones
- `SECOND-KNOWLEDGE-BRAIN.md` — research knowledge base, self-updating via crawl4ai
