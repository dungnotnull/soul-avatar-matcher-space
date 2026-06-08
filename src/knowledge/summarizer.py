"""
Paper relevance summarizer — scores and summarizes crawled research papers
against the project domain embedding.
"""

from __future__ import annotations

from src.personality.siamese_model import SiamesePersonalityModel

DOMAIN_EMBEDDING_TEXT = (
    "personality matching compatibility Big Five OCEAN Siamese network "
    "behavioral embedding agent-to-agent conversation"
)

MIN_RELEVANCE_SCORE = 0.70


class PaperSummarizer:
    """Ranks and filters crawled papers by relevance to the project domain."""

    def __init__(self):
        self._embedder: SiamesePersonalityModel | None = None

    def score_papers(self, papers: list[dict], max_entries: int = 20) -> list[dict]:
        scored = []
        for paper in papers:
            relevance = self._compute_relevance(paper.get("abstract", ""))
            if relevance >= MIN_RELEVANCE_SCORE:
                paper["relevance_score"] = round(relevance, 3)
                scored.append(paper)
        scored.sort(key=lambda p: p.get("relevance_score", 0), reverse=True)
        return scored[:max_entries]

    def _compute_relevance(self, text: str) -> float:
        try:
            if self._embedder is None:
                self._embedder = SiamesePersonalityModel()
            vec_a = self._embedder.encode_single(text)
            vec_b = self._embedder.encode_single(DOMAIN_EMBEDDING_TEXT)
            return float(
                sum(a * b for a, b in zip(vec_a, vec_b))
                / (
                    (sum(a * a for a in vec_a) ** 0.5)
                    * (sum(b * b for b in vec_b) ** 0.5)
                    + 1e-8
                )
            )
        except Exception:
            return 0.5

    def summarize(self, paper: dict) -> str:
        abstract = paper.get("abstract", "")
        if len(abstract) > 200:
            abstract = abstract[:197] + "..."
        return f"[{paper.get('source', 'unknown')}] {paper['title']} — {abstract}"
