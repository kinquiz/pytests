# login rate limiting
import time
from collections.abc import Callable


class LoginRateLimiter:
    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: float = 300.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._clock = clock  # injectable for tests
        self._failures: dict[str, list[float]] = {}

    def _recent(self, ip: str) -> list[float]:
        cutoff = self._clock() - self.window
        stamps = [t for t in self._failures.get(ip, []) if t > cutoff]
        if stamps:
            self._failures[ip] = stamps
        else:
            self._failures.pop(ip, None)  # prune empty entries
        return stamps

    def is_blocked(self, ip: str) -> bool:
        return len(self._recent(ip)) >= self.max_attempts

    def record_failure(self, ip: str) -> None:
        self._recent(ip)
        self._failures.setdefault(ip, []).append(self._clock())

    def reset(self, ip: str) -> None:
        self._failures.pop(ip, None)

    def retry_after(self, ip: str) -> float:
        stamps = self._recent(ip)
        if len(stamps) < self.max_attempts:
            return 0.0
        # until enough failures age out
        oldest_relevant = stamps[-self.max_attempts]
        return max(0.0, oldest_relevant + self.window - self._clock())

    def __len__(self) -> int:
        return len(self._failures)


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _limiter(**kwargs) -> tuple[LoginRateLimiter, FakeClock]:
    clock = FakeClock()
    return LoginRateLimiter(clock=clock, **kwargs), clock


def test_blocks_after_max_attempts():
    limiter, _ = _limiter(max_attempts=3, window_seconds=60)
    for _ in range(2):
        limiter.record_failure("1.2.3.4")
    assert not limiter.is_blocked("1.2.3.4")
    limiter.record_failure("1.2.3.4")
    assert limiter.is_blocked("1.2.3.4")


def test_ips_are_independent():
    limiter, _ = _limiter(max_attempts=1)
    limiter.record_failure("1.1.1.1")
    assert limiter.is_blocked("1.1.1.1")
    assert not limiter.is_blocked("2.2.2.2")


def test_window_slides():
    limiter, clock = _limiter(max_attempts=2, window_seconds=60)
    limiter.record_failure("ip")
    clock.advance(40)
    limiter.record_failure("ip")
    assert limiter.is_blocked("ip")
    assert limiter.retry_after("ip") == 20

    clock.advance(21)
    assert not limiter.is_blocked("ip")
    assert limiter.retry_after("ip") == 0


def test_reset_on_success():
    limiter, _ = _limiter(max_attempts=2)
    limiter.record_failure("ip")
    limiter.record_failure("ip")
    limiter.reset("ip")
    assert not limiter.is_blocked("ip")


def test_old_entries_are_cleaned_up():
    limiter, clock = _limiter(window_seconds=10)
    for i in range(50):
        limiter.record_failure(f"10.0.0.{i}")
    assert len(limiter) == 50
    clock.advance(11)
    for i in range(50):
        limiter.is_blocked(f"10.0.0.{i}")
    assert len(limiter) == 0
