"""In-process sliding-window rate limiter (per client IP + global cap).

Design notes: docs/INFRASTRUCTURE.md §5. Single-instance assumption; the
implementation must stay swappable for a Redis-backed one (v2.x).
"""

import time
from collections import deque
from math import ceil


class SlidingWindowLimiter:
    """Track request timestamps per key and enforce two caps per window."""

    WINDOW_SECONDS = 60.0

    def __init__(self) -> None:
        self._per_key: dict[str, deque[float]] = {}
        self._global: deque[float] = deque()

    def _prune(self, now: float) -> None:
        cutoff = now - self.WINDOW_SECONDS
        while self._global and self._global[0] <= cutoff:
            self._global.popleft()
        for key, hits in list(self._per_key.items()):
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                del self._per_key[key]

    def check(self, key: str, per_min: int, global_per_min: int) -> float | None:
        """Return None when allowed, else the seconds the client must wait."""
        now = time.monotonic()
        self._prune(now)

        blocked_until: float | None = None
        if len(self._global) >= global_per_min:
            blocked_until = self._global[0] + self.WINDOW_SECONDS
        else:
            hits = self._per_key.get(key, deque())
            if len(hits) >= per_min:
                blocked_until = hits[0] + self.WINDOW_SECONDS

        if blocked_until is not None:
            return max(1.0, ceil(blocked_until - now))

        self._per_key.setdefault(key, deque()).append(now)
        self._global.append(now)
        return None
