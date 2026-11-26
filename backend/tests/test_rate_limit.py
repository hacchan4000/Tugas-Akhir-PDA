"""Tes `SlidingWindowLimiter` (pembatas laju login).

Waktu dimajukan lewat `monkeypatch` pada `time.monotonic`, jadi tidak ada
`sleep` dan tes tetap cepat serta deterministik.
"""

from __future__ import annotations

import pytest

from app.utils import rate_limit
from app.utils.rate_limit import SlidingWindowLimiter


class _Jam:
    def __init__(self) -> None:
        self.sekarang = 1000.0

    def __call__(self) -> float:
        return self.sekarang


@pytest.fixture()
def jam(monkeypatch: pytest.MonkeyPatch) -> _Jam:
    jam = _Jam()
    monkeypatch.setattr(rate_limit.time, "monotonic", jam)
    return jam


def test_allows_until_limit_then_blocks(jam: _Jam) -> None:
    limiter = SlidingWindowLimiter(max_events=3, window_seconds=60)

    for _ in range(3):
        assert limiter.retry_after("1.2.3.4") == 0.0
        limiter.record("1.2.3.4")

    assert limiter.retry_after("1.2.3.4") > 0
    assert limiter.retry_after("5.6.7.8") == 0.0, "kunci lain tidak boleh terpengaruh"


def test_window_slides_after_expiry(jam: _Jam) -> None:
    limiter = SlidingWindowLimiter(max_events=2, window_seconds=60)
    limiter.record("ip")
    limiter.record("ip")
    assert limiter.retry_after("ip") > 0

    jam.sekarang += 59.9
    assert limiter.retry_after("ip") > 0

    jam.sekarang += 0.1
    assert limiter.retry_after("ip") == 0.0
    limiter.record("ip")
    assert limiter.retry_after("ip") == 0.0


def test_retry_after_reports_remaining_time(jam: _Jam) -> None:
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=30)
    limiter.record("ip")

    jam.sekarang += 10
    sisa = limiter.retry_after("ip")

    assert sisa == pytest.approx(20.0)


def test_reset_clears_one_key(jam: _Jam) -> None:
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=60)
    limiter.record("a")
    limiter.record("b")

    limiter.reset("a")

    assert limiter.retry_after("a") == 0.0
    assert limiter.retry_after("b") > 0


def test_memory_is_bounded(jam: _Jam) -> None:
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=60, max_keys=10)

    for i in range(50):
        limiter.record(f"ip-{i}")
        jam.sekarang += 0.01

    assert len(limiter) <= 10


def test_expired_keys_are_dropped(jam: _Jam) -> None:
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=10, max_keys=10)
    limiter.record("ip")
    assert len(limiter) == 1

    jam.sekarang += 11
    assert limiter.retry_after("ip") == 0.0
    assert len(limiter) == 0


@pytest.mark.parametrize(
    ("max_events", "window_seconds", "max_keys"),
    [(0, 1, 1), (1, 0, 1), (1, -1, 1), (1, 1, 0)],
)
def test_rejects_invalid_configuration(
    max_events: int, window_seconds: float, max_keys: int
) -> None:
    with pytest.raises(ValueError):
        SlidingWindowLimiter(
            max_events=max_events, window_seconds=window_seconds, max_keys=max_keys
        )
