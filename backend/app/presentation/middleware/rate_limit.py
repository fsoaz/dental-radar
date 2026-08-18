"""Redis-backed per-client rate limiting for expensive mutating routes."""

from __future__ import annotations

import hashlib
import ipaddress
import logging
from dataclasses import dataclass
from typing import Protocol

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

RATE_LIMITED_PREFIXES = (
    "/api/v1/clinics/discover",
    "/api/v1/scoring-config",
)
RATE_LIMITED_SUFFIXES = (
    "/signals:detect",
    "/enrich",
)

_INCREMENT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('PEXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('PTTL', KEYS[1])
return {count, ttl}
"""


@dataclass(frozen=True)
class RateLimitResult:
    count: int
    retry_after_seconds: int


class RateLimitStore(Protocol):
    async def increment(self, key: str, window_seconds: int) -> RateLimitResult: ...

    async def ping(self) -> None: ...

    async def close(self) -> None: ...


class RedisRateLimitStore:
    def __init__(self, redis_url: str) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=False)

    async def increment(self, key: str, window_seconds: int) -> RateLimitResult:
        count, ttl_ms = await self._redis.eval(
            _INCREMENT_SCRIPT,
            1,
            key,
            window_seconds * 1000,
        )
        retry_after = max(1, (int(ttl_ms) + 999) // 1000)
        return RateLimitResult(count=int(count), retry_after_seconds=retry_after)

    async def ping(self) -> None:
        await self._redis.ping()

    async def close(self) -> None:
        await self._redis.aclose()


def parse_trusted_proxies(raw: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse a comma-separated list of proxy IPs/CIDRs; ignore invalid entries."""
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
        store: RateLimitStore,
        limit: int = 30,
        window_seconds: int = 60,
        trusted_proxies: str = "",
    ) -> None:
        super().__init__(app)
        self._store = store
        self._limit = max(1, limit)
        self._window = max(1, window_seconds)
        self._trusted = parse_trusted_proxies(trusted_proxies)

    def _is_limited(self, path: str, method: str) -> bool:
        if method.upper() in {"GET", "HEAD"}:
            return False
        if any(path.startswith(prefix) for prefix in RATE_LIMITED_PREFIXES):
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

    @staticmethod
    def _bucket_key(client: str, path: str) -> str:
        digest = hashlib.sha256(f"{client}:{path}".encode()).hexdigest()
        return f"dental-radar:rate-limit:{digest}"

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not self._is_limited(path, request.method):
            return await call_next(request)

        key = self._bucket_key(self._client_key(request), path)
        try:
            result = await self._store.increment(key, self._window)
        except Exception:
            logger.exception("Redis rate limiter unavailable")
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "RATE_LIMIT_UNAVAILABLE",
                        "message": "Request cost controls are temporarily unavailable",
                        "details": None,
                    }
                },
            )

        if result.count > self._limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests; try again later",
                        "details": {"limit": self._limit, "window_seconds": self._window},
                    }
                },
                headers={"Retry-After": str(result.retry_after_seconds)},
            )
        return await call_next(request)
