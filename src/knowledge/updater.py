"""
Knowledge brain file updater — appends new research entries to SECOND-KNOWLEDGE-BRAIN.md
with date stamps and duplicate detection.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import datetime
from loguru import logger

from config.settings import settings

KNOWLEDGE_BRAIN_PATH = settings.PROJECT_ROOT / "SECOND-KNOWLEDGE-BRAIN.md"
UPDATE_MARKER = "---\n\n*Next scheduled auto-update:"


class KnowledgeBrainUpdater:
    """Updates SECOND-KNOWLEDGE-BRAIN.md with new entries."""

    def __init__(self, brain_path: Path | None = None):
        self.brain_path = brain_path or KNOWLEDGE_BRAIN_PATH

    def add_entries(
        self,
        papers: list[dict],
        summarizer=None,
    ) -> int:
        from src.knowledge.summarizer import PaperSummarizer

        summarizer = summarizer or PaperSummarizer()
        scored = summarizer.score_papers(papers)
        if not scored:
            logger.info("No new relevant papers to add.")
            return 0

        existing = self._read_existing()
        added = 0
        today = datetime.now().strftime("%Y-%m-%d")

        new_entries = []
        for paper in scored:
            entry_hash = hashlib.md5(paper["title"].encode()).hexdigest()
            if entry_hash in existing:
                continue

            entry = (
                f"### [{today}] — {paper['source']}\n"
                f"**Paper:** {paper['title']}\n"
                f"**Authors:** {paper['authors']}\n"
                f"**Year:** {paper['year']} | **Venue:** {paper['venue']}\n"
                f"**DOI/Link:** {paper['link']}\n"
                f"**Relevance:** {summarizer.summarize(paper)}\n\n"
            )
            new_entries.append(entry)
            added += 1

        if added > 0:
            self._insert_entries(new_entries, today)
            logger.info(f"Added {added} new entries to SECOND-KNOWLEDGE-BRAIN.md")

        return added

    def _read_existing(self) -> set:
        if not self.brain_path.exists():
            return set()
        content = self.brain_path.read_text(encoding="utf-8")
        hashes = set()
        for line in content.split("\n"):
            if line.startswith("**Paper:**"):
                hashes.add(hashlib.md5(line.encode()).hexdigest())
        return hashes

    def _insert_entries(self, entries: list[str], today: str):
        content = self.brain_path.read_text(encoding="utf-8")
        marker = UPDATE_MARKER
        if marker in content:
            insert_point = content.rindex(marker)
            prefix = content[:insert_point]
            suffix = content[insert_point:]
        else:
            prefix = content.rstrip() + "\n\n"
            suffix = f"\n---\n\n*Next scheduled auto-update: {today}*"

        new_section = "\n## Auto-Updated Entries\n\n" + "".join(entries)
        new_content = prefix.rstrip() + new_section + suffix
        self.brain_path.write_text(new_content, encoding="utf-8")
