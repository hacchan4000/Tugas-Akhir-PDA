"""Pembatas laju in-process (sliding window) untuk endpoint sensitif.

Dipakai `POST /auth/login` untuk mempersulit brute force password.

Batasan yang disengaja dan harus disebut di laporan:

- Hitungan hidup di memori proses, jadi hilang saat restart dan **tidak**
  dibagi antar worker. Untuk satu proses `uvicorn` itu memadai; kalau nanti
  dijalankan dengan beberapa worker, ganti dengan penyimpanan bersama (Redis).
- Kunci pembatas memakai alamat klien dari `request.client.host`. Di belakang
  reverse proxy, jalankan uvicorn dengan `--proxy-headers` dan
  `--forwarded-allow-ips` yang benar, kalau tidak semua pengunjung akan terlihat
  berasal dari IP proxy yang sama.
"""

from __future__ import annotations

import threading
import time
from collections import deque


class SlidingWindowLimiter:
    """Batasi jumlah kejadian per kunci dalam jendela waktu bergulir."""

    def __init__(
        self,
        max_events: int,
        window_seconds: float,
        *,
        max_keys: int = 4096,
    ) -> None:
        if max_events < 1:
            raise ValueError("max_events harus >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds harus > 0")
        if max_keys < 1:
            raise ValueError("max_keys harus >= 1")

        self._max_events = int(max_events)
        self._window = float(window_seconds)
        self._max_keys = int(max_keys)
        self._lock = threading.Lock()
        self._events: dict[str, deque[float]] = {}

    # -- publik ------------------------------------------------------------
    @property
    def max_events(self) -> int:
        return self._max_events

    @property
    def window_seconds(self) -> float:
        return self._window

    def retry_after(self, key: str) -> float:
        """0.0 bila masih boleh mencoba; selain itu sisa detik sampai boleh lagi."""
        now = time.monotonic()
        with self._lock:
            events = self._prune(key, now)
            if events is None or len(events) < self._max_events:
                return 0.0
            return max(0.0, events[0] + self._window - now)

    def record(self, key: str) -> None:
        """Catat satu kejadian (dipanggil hanya saat percobaan gagal)."""
        now = time.monotonic()
        with self._lock:
            events = self._prune(key, now)
            if events is None:
                if len(self._events) >= self._max_keys:
                    self._evict(now)
                events = deque()
                self._events[key] = events
            events.append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)

    # -- internal ----------------------------------------------------------
    def _prune(self, key: str, now: float) -> deque[float] | None:
        events = self._events.get(key)
        if events is None:
            return None
        batas = now - self._window
        while events and events[0] <= batas:
            events.popleft()
        if not events:
            self._events.pop(key, None)
            return None
        return events

    def _evict(self, now: float) -> None:
        """Jaga memori: buang kunci kedaluwarsa, lalu yang paling lama tidak aktif."""
        for key in list(self._events):
            self._prune(key, now)
        if len(self._events) < self._max_keys:
            return
        tertua = min(self._events, key=lambda k: self._events[k][-1])
        self._events.pop(tertua, None)


__all__ = ["SlidingWindowLimiter"]
