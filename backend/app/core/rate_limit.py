import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import TooManyRequests

_hits: dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # Behind Cloudflare/Nginx the socket IP is the proxy, so read the forwarded headers.
    forwarded = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def auth_rate_limit(request: Request) -> None:
    """Simple in-memory limiter for auth endpoints (fine for a single-container POC)."""
    now = time.monotonic()
    window = _hits[_client_ip(request)]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.RATE_LIMIT_PER_MINUTE:
        raise TooManyRequests()
    window.append(now)
