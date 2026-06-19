import httpx
import pytest

from app.infrastructure.crawler.website_crawler import (
    HttpxWebsiteCrawler,
    UnsafeUrlError,
    assert_public_url,
)


def test_assert_public_url_rejects_non_http_scheme():
    with pytest.raises(UnsafeUrlError):
        assert_public_url("file:///etc/passwd")


def test_assert_public_url_rejects_metadata_address():
    with pytest.raises(UnsafeUrlError):
        assert_public_url("http://169.254.169.254/latest/meta-data/")


def test_assert_public_url_rejects_loopback():
    with pytest.raises(UnsafeUrlError):
        assert_public_url("http://127.0.0.1:8000/")


def test_assert_public_url_allows_public_host():
    # Uses a documentation IP literal so no real DNS lookup leaves the box.
    assert_public_url("https://93.184.216.34/")


def test_crawler_blocks_redirect_to_internal_address():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "93.184.216.34":
            return httpx.Response(302, headers={"location": "http://169.254.169.254/"})
        raise AssertionError("crawler followed redirect to blocked host")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, follow_redirects=False)
    crawler = HttpxWebsiteCrawler(client=client)

    with pytest.raises(UnsafeUrlError):
        crawler.fetch("https://93.184.216.34/")
