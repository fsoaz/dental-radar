"""Simple in-memory per-IP rate limiter for expensive mutating routes."""

from __future__ import annotations

import ipaddress
import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Paths that hit billed third parties or rewrite business logic.
RATE_LIMITED_PREFIXES = (
    "/api/v1/clinics/discover",
    "/api/v1/scoring-config",
)
RATE_LIMITED_SUFFIXES = (
    "/signals:detect",
    "/enrich",
)

# Upper bound on distinct buckets held in memory. Keys derive from client
# addresses, so without a cap a caller cycling addresses grows this without end.
DEFAULT_MAX_TRACKED_KEYS = 10_000


def parse_trusted_proxies(raw: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse a comma-separated list of proxy IPs/CIDRs. Unparsable entries are dropped."""
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for entry in raw.split(","):
        candidate = entry.strip()
        if not candidate:
            continue
        try:
            networks.append(ipaddress.ip_network(candidate, strict=False))
        except ValueError:
            continue
    return networks


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        limit: int = 30,
        window_seconds: int = 60,
        trusted_proxies: str = "",
        max_tracked_keys: int = DEFAULT_MAX_TRACKED_KEYS,
    ) -> None:
        super().__init__(app)
        self._limit = max(1, limit)
        self._window = max(1, window_seconds)
        self._trusted = parse_trusted_proxies(trusted_proxies)
        self._max_keys = max(1, max_tracked_keys)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._last_prune = time.monotonic()
        self._lock = Lock()

    def _is_limited(self, path: str, method: str) -> bool:
        if method.upper() == "GET":
            return False
        if any(path.startswith(prefix) for prefix in RATE_LIMITED_PREFIXES):
            # GET /scoring-config is excluded above; PUT is limited.
            return True
        return any(path.endswith(suffix) for suffix in RATE_LIMITED_SUFFIXES)

    def _is_trusted(self, address: str) -> bool:
        if not self._trusted:
            return False
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        return any(ip in network for network in self._trusted)

    def _client_key(self, request: Request) -> str:
        """Resolve the caller address, honouring X-Forwarded-For only from trusted proxies.

        X-Forwarded-For is attacker-controlled on any request that does not
        arrive through our own proxy, so keying buckets on it unconditionally
        lets a caller reset their own limit by rotating the header. It is read
        only when the immediate peer is a configured proxy; the chain is then
        walked right-to-left and the first address no trusted proxy vouched for
        wins, because leftmost entries are the ones a client can forge.
        """
        peer = request.client.host if request.client else None
        if peer is None:
            return "unknown"
        if not self._is_trusted(peer):
            return peer

        forwarded = request.headers.get("x-forwarded-for", "")
        hops = [part.strip() for part in forwarded.split(",") if part.strip()]
        for hop in reversed(hops):
            try:
                ipaddress.ip_address(hop)
            except ValueError:
                continue
            if not self._is_trusted(hop):
                return hop
        return peer

    def _prune(self, now: float) -> None:
        """Drop buckets idle for a full window, then enforce the hard cap.

        Caller must hold the lock.
        """
        stale = [
            key for key, hits in self._hits.items() if not hits or now - hits[-1] >= self._window
        ]
        for key in stale:
            del self._hits[key]

        overflow = len(self._hits) - self._max_keys
        if overflow > 0:
            oldest = sorted(self._hits.items(), key=lambda item: item[1][-1])
            for key, _ in oldest[:overflow]:
                del self._hits[key]

        self._last_prune = now

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not self._is_limited(path, request.method):
            return await call_next(request)

        key = f"{self._client_key(request)}:{path}"
        now = time.monotonic()
        with self._lock:
            if now - self._last_prune >= self._window or len(self._hits) >= self._max_keys:
                self._prune(now)

            bucket = self._hits[key]
            while bucket and now - bucket[0] >= self._window:
                bucket.popleft()
            if len(bucket) >= self._limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": "Too many requests; try again later",
                            "details": {"limit": self._limit, "window_seconds": self._window},
                        }
                    },
                    headers={"Retry-After": str(self._window)},
                )
            bucket.append(now)

        return await call_next(request)
