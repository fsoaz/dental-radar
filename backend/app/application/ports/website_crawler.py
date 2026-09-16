from typing import Protocol

from app.domain.value_objects.page_evidence import PageEvidence


class WebsiteFetchError(Exception):
    """Raised when a website crawler cannot fetch a page."""

    def __init__(self, url: str, message: str) -> None:
        self.url = url
        super().__init__(f"Failed to fetch {url}: {message}")


class WebsiteCrawler(Protocol):
    def fetch(self, url: str) -> PageEvidence:
        """Fetch a clinic website and extract crawl evidence."""
