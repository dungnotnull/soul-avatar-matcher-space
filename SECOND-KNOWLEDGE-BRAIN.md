# SECOND-KNOWLEDGE-BRAIN.md — soul-avatar-matcher

> Self-improving knowledge base. Updated weekly by crawl4ai pipeline.
> Last manual seed: 2026-06-03

---

## Core Concepts & Theoretical Foundations

### Personality Psychology Frameworks
| Framework | Key Dimensions | Relevance |
|-----------|---------------|---------|
| **Big Five (OCEAN)** | Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism | Primary personality model; most empirically validated; used as feature basis |
| **MBTI (Myers-Briggs)** | 16 types (E/I, S/N, T/F, J/P) | Secondary layer; less scientifically rigorous but widely recognized by users |
| **HEXACO** | Honesty-Humility, Emotionality, eXtraversion, Agreeableness, Conscientiousness, Openness | Extended Big Five; Honesty-Humility dimension valuable for value alignment |
| **Attachment Theory** | Secure, Anxious, Avoidant, Disorganized | Predicts relationship dynamics; complement to personality-based matching |
| **Relationship Science: Similarity-Attraction** | Byrne (1971); Luo & Klohnen (2005) | Similar values → attraction; similar Big Five → relationship quality; complementary E/I pairs → stability |

### Key Matching Hypotheses
1. **Similarity-Attraction Effect** (Byrne, 1971): people are more attracted to those who share similar attitudes and values
2. **Complementarity for Dominance** (Tiedens & Fragale, 2003): complementary dominance (assertive + deferential) predicts better interpersonal outcomes in some contexts
3. **Behavioral Inference Superiority** (Youyou et al., 2015): computational personality models trained on digital behavior outperform self-report assessments and human friends in accuracy
4. **Contrastive Learning for Personality** (modern ML): pairs of texts from the same person should embed closely; pairs from incompatible people should embed far apart — justifies Siamese architecture

---

## Key Research Papers

| Title | Authors | Year | Venue | DOI / Link | Relevance |
|-------|---------|------|-------|-----------|---------|
| Computer-based personality judgments are more accurate than those made by humans | Youyou, W. et al. | 2015 | PNAS | https://doi.org/10.1073/pnas.1418680112 | Core justification: behavioral data > self-report for personality modeling |
| Personality prediction from text: An overview | Majumder, N. et al. | 2017 | IJCAI | https://arxiv.org/abs/1709.05397 | Survey of text-to-Big-Five prediction methods |
| Predicting personality from book preferences with collaborative filtering | Nave, G. et al. | 2018 | Psychological Methods | https://doi.org/10.1037/met0000135 | Collaborative filtering applied to personality prediction |
| Deep Neural Networks Are More Accurate than Humans at Detecting Sexual Orientation from Facial Images | Wang & Kosinski | 2018 | JPSP | — | Controversial but relevant: deep learning's power to infer latent human traits |
| Personality-Adaptive Conversational Agents | Mairesse, F. & Walker, M. | 2010 | JAIR | https://doi.org/10.1613/jair.2905 | Foundational work on personality-responsive NLP agents |
| Siamese Recurrent Architectures for Learning Sentence Similarity | Mueller, J. & Thyagarajan, A. | 2016 | AAAI | https://arxiv.org/abs/1512.00814 | Siamese network baseline for sentence/text similarity — directly applicable |
| Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks | Reimers, N. & Gurevych, I. | 2019 | EMNLP | https://arxiv.org/abs/1908.10084 | SBERT — base architecture for personality vector encoder |
| Personality detection from social media texts: A comparative study | Kazameini, A. et al. | 2020 | arXiv | https://arxiv.org/abs/2004.11000 | Comparative benchmark: BERT vs traditional ML for Big Five from social media |
| Can LLMs Predict Human Personality? | Rao, G. et al. | 2023 | arXiv | https://arxiv.org/abs/2307.14614 | LLMs as personality assessors; implications for avatar reasoning capability |
| Beyond Similarity: Personality Complementarity in Romantic Relationships | Dyrenforth, P.S. et al. | 2010 | Personality and Social Psychology Review | https://doi.org/10.1177/1088868310371079 | Complementarity vs. similarity; guides scorer design |
| Private Traits and Attributes Are Predictable from Digital Records of Human Behavior | Kosinski, M. et al. | 2013 | PNAS | https://doi.org/10.1073/pnas.1218772110 | Foundational: digital behavior → personality traits; privacy considerations |

---

## State-of-the-Art ML/DL Models

### Personality Prediction Models
| Model ID | Venue / Year | Task | Papers with Code | Notes |
|----------|-------------|------|-----------------|-------|
| `Minej/bert-base-personality` | HuggingFace 2022 | Big Five from text | — | Direct use in Phase 1; best open-source Big Five predictor |
| `lxyuan/distilbert-base-multilingual-cased-sentiments-student` | HuggingFace | Multilingual sentiment | — | For Vietnamese + English behavioral text |
| `google/gemma-2-2b-it` | Google 2024 | General instruction following | — | Alternative local SLM via Ollama |

### Embedding Models (Personality Vector Space)
| Model ID | Benchmark | Use Case | Notes |
|----------|-----------|---------|-------|
| `BAAI/bge-large-en-v1.5` | MTEB #1 English (2024) | Primary personality vector encoder | Best quality/speed tradeoff |
| `sentence-transformers/all-MiniLM-L6-v2` | MTEB top-20 | Fast embedding for high-volume A2A | 5× faster than bge-large; use for parallel sessions |
| `intfloat/multilingual-e5-large` | MTEB multilingual | Vietnamese + English behavioral text | Needed for VN language support |

### Emotion Detection Models
| Model ID | Classes | Use Case |
|----------|---------|---------|
| `j-hartmann/emotion-english-distilroberta-base` | 7 (joy, sadness, anger, fear, surprise, disgust, neutral) | Primary emotion feature extractor |
| `SamLowe/roberta-base-go_emotions` | 28 fine-grained emotions | High-resolution emotion fingerprint |

### Local SLM Options (Ollama)
| Model | Parameters | Context | Quality | Use |
|-------|------------|---------|---------|-----|
| `qwen2.5:1.5b` | 1.5B | 32K | Good | Primary; fastest |
| `phi3:mini` | 3.8B | 128K | Better | Secondary; more capable |
| `llama3.2:3b` | 3B | 128K | Good | Fallback |

---

## Tools, Libraries & Frameworks

| Tool | GitHub | Use Case |
|------|--------|---------|
| **sentence-transformers** | https://github.com/UKPLab/sentence-transformers | Personality vector embedding; fine-tuning Siamese models |
| **Ollama** | https://github.com/ollama/ollama | Local SLM serving; avatar reasoning runtime |
| **grpcio** | https://github.com/grpc/grpc | A2A transport protocol |
| **pysqlcipher3** | https://github.com/rigglemania/pysqlcipher3 | AES-256 encrypted SQLite for personality vault |
| **crawl4ai** | https://github.com/unclecode/crawl4ai | Self-update crawler for research papers |
| **PyTorch** | https://github.com/pytorch/pytorch | Siamese Network training |
| **scikit-learn** | https://github.com/scikit-learn/scikit-learn | Cosine similarity, clustering, evaluation |
| **anthropic** | https://github.com/anthropics/anthropic-sdk-python | Claude API for report generation |
| **FastAPI** | https://github.com/tiangolo/fastapi | REST API for data ingestion from folder 3/5 |
| **MBTI-Detector** | https://huggingface.co/Elron/bleurt-base-512 | MBTI personality type classification |
| **personality-detection** | https://github.com/jcl132/personality-detection | Reference implementation for Big Five from essays |

---

## Self-Update Protocol

### crawl4ai Crawler Configuration
```python
CRAWL_TARGETS = [
    # ArXiv
    {"source": "arxiv", "categories": ["cs.AI", "cs.LG", "cs.CL"],
     "queries": ["personality computing", "compatibility prediction neural",
                 "Siamese network personality", "psychological trait NLP",
                 "A2A agent conversation", "cognitive compatibility AI"]},

    # Semantic Scholar
    {"source": "semantic_scholar",
     "queries": ["personality prediction from text 2024",
                 "deep learning compatibility matching",
                 "behavioral personality fingerprinting",
                 "Big Five OCEAN neural network"]},

    # HuggingFace Papers
    {"source": "huggingface_papers",
     "tags": ["personality", "compatibility", "social-ai", "behavioral-modeling"]},

    # Google Scholar
    {"source": "google_scholar",
     "queries": ["AI personality matching 2024", "cognitive compatibility machine learning",
                 "digital behavioral personality 2025"]},
]

UPDATE_FREQUENCY = "weekly"  # every Monday 02:00 local time
MIN_RELEVANCE_SCORE = 0.7    # cosine similarity to domain embedding
MAX_NEW_ENTRIES_PER_RUN = 20
```

### Domain Embedding (for relevance scoring)
Seed text: *"personality matching compatibility Big Five OCEAN Siamese network behavioral embedding agent-to-agent conversation"*

### Update Procedure
1. Crawler fetches new papers from all sources
2. Each paper abstract embedded via `all-MiniLM-L6-v2`
3. Cosine similarity computed against domain embedding
4. Papers with score > `MIN_RELEVANCE_SCORE` added to this file under **Knowledge Update Log**
5. HuggingFace Hub queried for new models with tags: `personality`, `compatibility`, `behavioral`
6. New models added to State-of-the-Art table with date stamp
7. Duplicate detection: skip entries with matching DOI or title similarity > 0.95

### Adding New Entries (Format)
```markdown
### [YYYY-MM-DD] — {source}
**Paper:** {Title}
**Authors:** {Authors}
**Year:** {Year} | **Venue:** {Venue}
**DOI/Link:** {link}
**Relevance:** {one-line note on why this matters for soul-avatar-matcher}
```

---

## Knowledge Update Log

### [2026-06-03] — Manual Seed
Initial knowledge base populated manually.
Sources surveyed: Google Scholar, ArXiv, Semantic Scholar, HuggingFace Hub.
Domain coverage: Big Five personality psychology, Siamese Networks, behavioral personality inference, compatibility prediction, A2A agent systems.
Models catalogued: 8 HuggingFace models across personality prediction, embedding, emotion detection, and local SLM categories.
Papers catalogued: 11 foundational papers spanning 2010–2023.

---

*Next scheduled auto-update: 2026-06-10 (first Monday after project initialization)*
*Crawler script: `scripts/weekly_knowledge_update.py`*
*Update log entries are prepended (newest first) after manual seed section.*
