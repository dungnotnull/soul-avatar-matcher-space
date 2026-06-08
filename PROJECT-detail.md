# PROJECT-detail.md — soul-avatar-matcher

## Executive Summary
soul-avatar-matcher is a privacy-first AI compatibility engine that replaces shallow profile-based matching with deep cognitive alignment. It creates a continuously-updated **Cognitive Twin** (an AI avatar representing the user's personality, worldview, and communication patterns) and deploys it to autonomously conduct thousands of Agent-to-Agent (A2A) "conversations" with other users' twins. Only after two twins exceed a compatibility threshold — and both humans give explicit consent — are real identities revealed. The result is a small, curated list of soul-level matches instead of an endless swipe carousel.

---

## Problem Statement
Modern dating and social connection platforms optimize for engagement metrics, not meaningful compatibility. The research tells a clear story:

- ~50% of online dating app users report feeling frustrated with low match quality despite high usage (Pew Research, 2023)
- Personality similarity on core traits (Big Five dimensions: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) is a significantly stronger predictor of long-term relationship satisfaction than demographic similarity (Botwin et al., 1997; Luo & Klohnen, 2005)
- Survey-based personality tests produce inflated, socially desirable self-reports; behavioral inference from natural digital activity yields more accurate personality profiles (Youyou et al., 2015 — Cambridge Psychographics study)
- The average person spends 5–10 hours per week on dating apps, yet only 12% report meeting a meaningful long-term partner via these platforms (Statista, 2024)

**Core hypothesis:** If two people's *thinking patterns and value systems* are compatible at a deep cognitive level, a real-world connection will be more fulfilling and durable — regardless of superficial attributes. An AI twin that negotiates compatibility on your behalf — privately, autonomously, at scale — can surface these rare matches without requiring you to perform for an audience.

---

## Target Users & Use Cases
| User Type | Use Case |
|-----------|---------|
| Professionals (25–45) with limited time | Delegate the "search phase" to an AI twin; only invest time in highly-filtered matches |
| Introverts / socially anxious individuals | Interact through an avatar first; lower the activation energy for real-world connection |
| Users of omni-presence-soulmate (folder 5) | Seamless data integration; no manual setup required |
| Users seeking intellectual/philosophical compatibility | Prioritize worldview alignment over physical appearance |
| Privacy-conscious users | All raw data stays local; only an anonymized vector and behavioral fingerprint are ever shared |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  USER'S LOCAL DEVICE                    │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐  │
│  │ Data Sources │    │     Personality Engine       │  │
│  │              │    │                              │  │
│  │ • Folder 5   │───▶│  Big Five Trait Extractor    │  │
│  │   (presence) │    │  (Minej/bert-base-personality│  │
│  │ • Folder 3   │    │                              │  │
│  │   (knowledge │    │  Siamese Neural Network      │  │
│  │    graph)    │    │  → 512-dim Personality Vector│  │
│  │ • Chat logs  │    │                              │  │
│  │ • Music/film │    │  Nightly Update Loop         │  │
│  │   history    │    │  (drift detection + refit)   │  │
│  └──────────────┘    └──────────────┬───────────────┘  │
│                                     │                   │
│                      ┌──────────────▼───────────────┐  │
│                      │       Local SLM (Ollama)      │  │
│                      │  Qwen2.5-1.5B / Phi-3-mini    │  │
│                      │  → Avatar Reasoning Engine    │  │
│                      └──────────────┬───────────────┘  │
│                                     │                   │
│                      ┌──────────────▼───────────────┐  │
│                      │     Avatar Capsule Builder    │  │
│                      │  • Personality vector         │  │
│                      │  • Anonymized fingerprint     │  │
│                      │  • Debate stance generator    │  │
│                      └──────────────┬───────────────┘  │
└─────────────────────────────────────┼───────────────────┘
                                      │ AES-256 encrypted gRPC
                        ┌─────────────▼──────────────────┐
                        │    A2A Dating Network (P2P)     │
                        │                                 │
                        │  Avatar ◄────────────► Avatar   │
                        │  (User A)   Debate    (User B)  │
                        │                                 │
                        │  Topics: finance, lifestyle,    │
                        │  conflict resolution, values,   │
                        │  creativity, risk appetite...   │
                        └─────────────┬──────────────────┘
                                      │
                        ┌─────────────▼──────────────────┐
                        │     Compatibility Scorer        │
                        │                                 │
                        │  • Cosine similarity on vectors │
                        │  • LLM-judged dialogue quality  │
                        │  • Complementarity bonus        │
                        │  • Weighted composite score     │
                        └─────────────┬──────────────────┘
                                      │ Score > threshold
                        ┌─────────────▼──────────────────┐
                        │       Consent Gate              │
                        │                                 │
                        │  1. Anonymized report to User A │
                        │  2. Anonymized report to User B │
                        │  3. Both press "Match"          │
                        │  4. Contact info unlocked       │
                        │  5. Shared-interest venue suggestion │
                        └────────────────────────────────┘
```

---

## Tech Stack
| Component | Technology | Source |
|-----------|-----------|--------|
| Language | Python 3.11+ | — |
| Personality vector model | PyTorch Siamese Network (custom) | Trained on Big Five datasets |
| Trait extractor | `Minej/bert-base-personality` | HuggingFace |
| Sentence embeddings | `BAAI/bge-large-en-v1.5` | HuggingFace |
| Emotion detection | `j-hartmann/emotion-english-distilroberta-base` | HuggingFace |
| Local SLM runtime | Ollama | https://ollama.ai |
| Primary local SLM | Qwen2.5-1.5B-Instruct | Ollama model library |
| A2A transport | gRPC + Protocol Buffers | grpcio, protobuf |
| Local database | SQLite + SQLCipher (AES-256) | pysqlcipher3 |
| Compatibility scoring | scikit-learn (cosine_similarity) + custom LLM judge | pip |
| External LLM (reports) | Claude API / GPT-4o | anthropic, openai SDK |
| Data ingestion | REST API calls to folder 3 & 5 agents | httpx |
| Self-update crawler | crawl4ai | https://github.com/unclecode/crawl4ai |
| Serialization | Protobuf | google-protobuf |
| API server | FastAPI + uvicorn | pip |
| Config management | python-dotenv + pydantic-settings | pip |

---

## ML/DL Models

### Primary Models
| Model | Source | Purpose | Fine-tuning Needed? |
|-------|--------|---------|-------------------|
| Siamese Neural Network | Custom PyTorch | Encode personality → 512-dim vector | Yes — train on Big Five labeled conversation pairs |
| `Minej/bert-base-personality` | HuggingFace | Predict Big Five scores from text samples | No — use as-is; backbone for feature extraction |
| `BAAI/bge-large-en-v1.5` | HuggingFace | General-purpose sentence embedding for behavioral text | No |
| `j-hartmann/emotion-english-distilroberta-base` | HuggingFace | 7-class emotion detection from messages | No |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | HuggingFace | Sentiment polarity from behavioral streams | No |

### Siamese Network Architecture
```
Input: pair of behavioral text sequences (user A, user B)
    │
    ▼
Shared Encoder (fine-tuned BERT backbone)
    │
    ▼
512-dim Personality Vector (L2-normalized)
    │
    ▼
Contrastive Loss (compatible pairs = similar vectors)
    │
    ▼
Training data: Big Five dataset + synthetic compatible/incompatible pairs
```

### Training Data Sources
- **Open Psychometrics Big Five dataset** (1M+ responses with personality labels)
- **Essays dataset** (Mairesse et al., 2007) — 2,468 essays with Big Five annotations
- **PersonalityDB** (social media posts + MBTI labels)
- Synthetic pair generation: use GPT-4o to generate "debate" dialogue pairs with known compatibility scores

---

## External LLM API Integration

### Pluggable LLM Backend Design
```python
LLM_PROVIDER = "ollama"  # options: "ollama", "claude", "openai"
```

| Provider | Use Case | When to Use |
|----------|---------|------------|
| Ollama (Qwen2.5-1.5B) | A2A avatar reasoning, always-on | Default; privacy-critical path |
| Claude API (Sonnet 4.6) | Compatibility report narrative generation | When user opts in; premium quality |
| GPT-4o | Alternative report generation | Fallback if Claude unavailable |

**Graceful fallback chain:** `claude → openai → ollama (report mode)`
**Privacy contract:** Only the anonymized compatibility report is generated via external API; no raw user data, chat logs, or personality scores are sent.

---

## Feature Specification

### MVP Features
- [ ] Big Five personality trait extraction from text samples
- [ ] Siamese Network training pipeline (Big Five dataset)
- [ ] Local personality vector storage (AES-256 encrypted SQLite)
- [ ] Avatar capsule builder (vector + anonymized fingerprint)
- [ ] A2A gRPC session handler (simulate 2-agent debate on 5 fixed topics)
- [ ] Cosine similarity compatibility scorer
- [ ] CLI consent gate (display anonymized report, accept/reject)
- [ ] Nightly personality matrix update (new behavioral data → vector refresh)
- [ ] Data ingestion from folder 3 and folder 5 (or manual text input fallback)

### Advanced Features
- [ ] Thousands of parallel A2A sessions (async gRPC + connection pool)
- [ ] Dynamic debate topic selection based on personality profiles
- [ ] Complementarity scoring (oppositeness bonus for specific Big Five dimensions)
- [ ] LLM-judged dialogue quality score (separate from cosine distance)
- [ ] Weighted composite compatibility score (tunable per user preference)
- [ ] Venue suggestion engine (shared interest analysis → location recommendation)
- [ ] Web dashboard (React or Streamlit) for match review
- [ ] Personality vector drift alert (notify user if self changes significantly)
- [ ] MBTI classification layer on top of Big Five scores
- [ ] Multi-language support (Vietnamese + English behavioral text)
- [ ] federated P2P matching network (integration with folder 1 infrastructure)

---

## Full E2E Data Flow

1. **Behavioral data arrives** from folder 5 (presence agent) and folder 3 (knowledge graph) via local REST API; fallback: user pastes chat exports or journal entries
2. **Trait extractor** runs `Minej/bert-base-personality` on text windows → produces (O, C, E, A, N) trait scores
3. **Emotion detector** tags emotional valence and intensity across the text stream
4. **Siamese encoder** ingests trait scores + emotion features → outputs 512-dim L2-normalized personality vector
5. **Personality vault** stores vector in AES-256 encrypted SQLite; timestamp + drift delta logged
6. **Avatar capsule builder** packages: personality vector, anonymized ID, behavioral fingerprint hash, SLM model endpoint
7. **A2A session manager** connects two avatar capsules via encrypted gRPC; local SLM generates responses to structured debate topics
8. **Debate loop runs** for N rounds per topic (finance, conflict, creativity, lifestyle, values); each response stored as a transcript hash only
9. **Compatibility scorer** computes: (a) cosine similarity between personality vectors, (b) LLM judge score on dialogue coherence, (c) weighted composite
10. **Threshold check**: if composite score < 90%, session closed silently; if ≥ 90%, proceed to consent gate
11. **Consent gate**: anonymized report sent to User A and User B independently; both must confirm
12. **Match reveal**: contact information unlocked; shared-interest venue suggested based on overlapping knowledge graph nodes from folder 3

---

## Privacy & Security

| Concern | Mitigation |
|---------|-----------|
| Raw behavioral data exposure | Stays on device; never transmitted |
| Personality vector linkability | Only vector transmitted; no demographic data attached |
| A2A eavesdropping | TLS 1.3 + application-layer AES-256 on all gRPC streams |
| Avatar impersonation | Capsule signed with user's local private key (Ed25519) |
| Data at rest | SQLCipher AES-256 on all local databases |
| External LLM exposure | Only anonymized compatibility report text sent to Claude/GPT; no raw data |
| Consent bypass | Bilateral confirmation required; no unilateral reveal possible |

---

## Key Python Dependencies
```
# Core ML
torch>=2.2.0
transformers>=4.40.0
sentence-transformers>=3.0.0
scikit-learn>=1.4.0
numpy>=1.26.0

# A2A Protocol
grpcio>=1.63.0
grpcio-tools>=1.63.0
protobuf>=4.25.0

# Database
pysqlcipher3>=1.2.0

# API & Config
fastapi>=0.111.0
uvicorn>=0.29.0
httpx>=0.27.0
pydantic-settings>=2.2.0
python-dotenv>=1.0.0

# External LLMs
anthropic>=0.28.0
openai>=1.30.0

# Self-update
crawl4ai>=0.3.0

# Utilities
loguru>=0.7.0
rich>=13.7.0
```

---

## Improvement Suggestions (Beyond Original Idea)

1. **Complementarity scoring** — not just similarity; for some Big Five dimensions (e.g., Extraversion × Introversion) complementarity predicts better long-term outcomes than similarity. Weight accordingly.
2. **Longitudinal vector tracking** — alert users when their own personality vector shifts significantly over months; this is a self-insight feature, not just a matching tool.
3. **"Values conflict simulation"** — A2A sessions should include deliberately contentious scenarios (financial crisis, family conflict) to stress-test compatibility under pressure, not just pleasant conversations.
4. **Group compatibility** — extend to friend-group finding (N-way compatibility for social circles, not just dyadic matching).
5. **Compatibility explanation layer** — when a match is found, generate a plain-language explanation of *why* these two vectors are compatible, with specific behavioral evidence.
6. **Temporal A2A** — run the same A2A session at multiple points over weeks; if compatibility score remains stable or improves, confidence in the match increases.
7. **Privacy-preserving federated matching** — use Secure Multi-Party Computation (MPC) so that personality vectors are never transmitted in plaintext, even for similarity computation.
8. **Anti-gaming protection** — detect users who manually craft their behavioral input to game the personality vector; flag anomalous update patterns.
9. **Opt-in demographic compatibility layer** — for users who want basic demographic filters, add them as a post-filter on top of cognitive compatibility (not the primary signal).
10. **Integration with folder 1 (decentralized-agent-mesh)** — use the DID/P2P infrastructure from folder 1 as the identity and transport layer for the A2A dating network in production.
