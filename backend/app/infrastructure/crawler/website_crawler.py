import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse

import httpx

from app.application.dto.page_evidence import PageEvidence
from app.application.ports.website_crawler import WebsiteCrawler

ALLOWED_SCHEMES = frozenset({"http", "https"})
MAX_REDIRECTS = 5


class WebsiteFetchError(Exception):
    def __init__(self, url: str, message: str) -> None:
        self.url = url
        super().__init__(f"Failed to fetch {url}: {message}")


class UnsafeUrlError(WebsiteFetchError):
    """Raised when a URL targets a disallowed scheme or non-public address."""


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _resolve_public_address(url: str) -> tuple[str, str, int | None]:
    """Resolve host to a validated public IP, returning (ip, host, explicit_port).

    Raises UnsafeUrlError for disallowed schemes or hosts resolving to
    private/link-local/etc ranges (e.g. cloud metadata at 169.254.169.254).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeUrlError(url, f"disallowed scheme '{parsed.scheme}'")

    host = parsed.hostname
    if not host:
        raise UnsafeUrlError(url, "missing host")

    try:
        resolved = socket.getaddrinfo(host, parsed.port or None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeUrlError(url, f"DNS resolution failed: {exc}") from exc

    if not resolved:
        raise UnsafeUrlError(url, "DNS resolution returned no addresses")

    for family, _type, _proto, _canon, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        if _is_blocked_ip(ip):
            raise UnsafeUrlError(url, f"host resolves to non-public address {ip}")

    return resolved[0][4][0], host, parsed.port


def assert_public_url(url: str) -> None:
    """Reject non-http(s) schemes and hosts that resolve to private/link-local ranges.

    Defends against SSRF (e.g. cloud metadata at 169.254.169.254, internal services).
    """
    _resolve_public_address(url)


def _pin_request_url(url: str, ip: str, port: int | None) -> str:
    """Rewrite url's host to the already-validated ip, preserving path/query/port."""
    parsed = urlparse(url)
    netloc = f"[{ip}]" if ":" in ip else ip
    if port:
        netloc = f"{netloc}:{port}"
    return urlunparse(parsed._replace(netloc=netloc))


class _LinkTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.meta: dict[str, str] = {}
        self.scripts: list[str] = []
        self._capture_script = False
        self._script_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        if tag == "a" and "href" in attr_map:
            self.links.append(attr_map["href"])
        if tag == "meta":
            name = attr_map.get("name") or attr_map.get("property") or ""
            content = attr_map.get("content") or ""
            if name:
                self.meta[name.lower()] = content
        if tag == "script":
            self._capture_script = True
            self._script_chunks = []

    def handle_data(self, data: str) -> None:
        if self._capture_script:
            self._script_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._capture_script:
            self.scripts.append("".join(self._script_chunks))
            self._capture_script = False


def normalize_website_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        return f"https://{url.strip()}"
    return url.strip()


def parse_page_evidence(url: str, html: str) -> PageEvidence:
    parser = _LinkTextParser()
    parser.feed(html)

    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
    absolute_links = [urljoin(url, link) for link in parser.links]

    return PageEvidence(
        url=url,
        html=html,
        text=text,
        scripts=parser.scripts,
        meta=parser.meta,
        links=absolute_links,
    )


class HttpxWebsiteCrawler(WebsiteCrawler):
    def __init__(self, *, client: httpx.Client | None = None, timeout: float = 10.0) -> None:
        # Redirects are followed manually so each hop can be re-validated against
        # the SSRF allowlist; never let httpx follow them automatically.
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=False)
        self._owns_client = client is None

    def fetch(self, url: str) -> PageEvidence:
        current = normalize_website_url(url)
        try:
            for _ in range(MAX_REDIRECTS + 1):
                # Resolve+validate and pin the request to that exact IP so httpx's
                # own connect-time DNS lookup can't be rebound to a different
                # (private) address after the check above passes.
                ip, host, port = _resolve_public_address(current)
                pinned_url = _pin_request_url(current, ip, port)
                response = self._client.get(
                    pinned_url,
                    headers={"Host": host},
                    extensions={"sni_hostname": host},
                )
                if response.is_redirect and response.has_redirect_location:
                    current = urljoin(current, response.headers["location"])
                    continue
                response.raise_for_status()
                return parse_page_evidence(current, response.text)
        except UnsafeUrlError:
            raise
        except httpx.HTTPError as exc:
            raise WebsiteFetchError(current, str(exc)) from exc

        raise WebsiteFetchError(current, f"exceeded {MAX_REDIRECTS} redirects")

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
