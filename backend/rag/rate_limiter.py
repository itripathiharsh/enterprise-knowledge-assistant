"""
Async rate limiter for Gemini API — 15 RPM token bucket.
Wraps all Gemini calls. Thread-safe via asyncio.Lock.
"""
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class GeminiRateLimiter:
    """
    Token bucket: 15 requests per 60 seconds.
    Each request consumes 1 token. Tokens refill over time.
    """
    def __init__(self, rpm: int = 14):  # Use 14 to stay safely under 15
        self.rpm = rpm
        self.min_interval = 60.0 / rpm  # seconds between requests
        self._lock = asyncio.Lock()
        self._last_request_time = 0.0

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            wait = self._last_request_time + self.min_interval - now
            if wait > 0:
                logger.debug(f"Rate limiter: waiting {wait:.2f}s")
                await asyncio.sleep(wait)
            self._last_request_time = time.monotonic()

_limiter = GeminiRateLimiter(rpm=14)

async def with_rate_limit(coro):
    """Wrap any async coroutine with rate limiting + exponential backoff retry."""
    max_retries = 3
    for attempt in range(max_retries):
        await _limiter.acquire()
        try:
            return await coro
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 2 ** attempt * 5  # 5s, 10s, 20s
                logger.warning(f"Gemini 429. Retry {attempt+1}/{max_retries} in {wait}s")
                await asyncio.sleep(wait)
            else:
                raise
    raise RuntimeError("Gemini API rate limit exceeded after retries.")
