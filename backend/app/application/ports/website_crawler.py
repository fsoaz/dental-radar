from typing import Protocol

from app.application.dto.page_evidence import PageEvidence


class WebsiteCrawler(Protocol):
    def fetch(self, url: str) -> PageEvidence:
        """Fetch a clinic website and extract crawl evidence."""
