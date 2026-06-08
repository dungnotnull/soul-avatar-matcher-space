#!/usr/bin/env python
"""
Weekly knowledge update entry point for cron/scheduler.

Runs the knowledge pipeline:
1. Crawl ArXiv, Semantic Scholar, HuggingFace Hub via APIs
2. Score papers for relevance using domain embedding
3. Update SECOND-KNOWLEDGE-BRAIN.md with new entries
4. Send notification via NotificationService
"""

import sys
from loguru import logger

from config.settings import settings
from src.knowledge.crawler import KnowledgeCrawler
from src.knowledge.summarizer import PaperSummarizer
from src.knowledge.updater import KnowledgeBrainUpdater
from src.knowledge.notifications import notification_service, NotificationLevel


def main():
    logger.info("=" * 50)
    logger.info("WEEKLY KNOWLEDGE UPDATE — soul-avatar-matcher")
    logger.info("=" * 50)

    crawler = KnowledgeCrawler()
    summarizer = PaperSummarizer()
    updater = KnowledgeBrainUpdater()

    try:
        papers = crawler.crawl()
        logger.info(f"Crawled {len(papers)} papers from all sources.")
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        notification_service.notify(
            level=NotificationLevel.ALERT,
            category="knowledge",
            title="Knowledge crawl failed",
            body=str(e),
        )
        crawler.close()
        return 1

    try:
        added = updater.add_entries(papers, summarizer)
    except Exception as e:
        logger.error(f"Update failed: {e}")
        notification_service.notify(
            level=NotificationLevel.ALERT,
            category="knowledge",
            title="Knowledge base update failed",
            body=str(e),
        )
        crawler.close()
        return 1

    crawler.close()

    if added > 0:
        logger.info(f"Weekly update complete: {added} new entries added.")
        notification_service.notify_knowledge_update(added, papers[:5])
    else:
        logger.info("Weekly update complete: no new relevant entries found.")
        notification_service.notify(
            level=NotificationLevel.INFO,
            category="knowledge",
            title="Knowledge update: no new entries",
            body="No new papers above relevance threshold were found this week.",
        )

    notification_service.notify_system_health("knowledge_crawler", True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
