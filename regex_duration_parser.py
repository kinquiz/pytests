# regex duration parser
import re
from datetime import timedelta

# repeated parts, e.g. 1h30m
_PART = re.compile(r"(\d+)\s*([smhdw])", re.IGNORECASE)
_FULL = re.compile(r"^\s*(?:\d+\s*[smhdw]\s*)+$", re.IGNORECASE)

_UNITS = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}

MAX_DURATION = timedelta(days=28)  # discord timeout limit


def parse_duration(text: str) -> timedelta:
    # findall alone would skip junk like 10x5m
    if not text or not _FULL.match(text):
        raise ValueError(f"invalid duration: {text!r}")

    total = timedelta()
    for amount, unit in _PART.findall(text):
        total += timedelta(**{_UNITS[unit.lower()]: int(amount)})

    if total <= timedelta(0):
        raise ValueError("duration must be greater than zero")
    if total > MAX_DURATION:
        raise ValueError(f"duration can't be longer than {MAX_DURATION.days} days")
    return total


def format_duration(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    parts = []
    for name, size in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        amount, seconds = divmod(seconds, size)
        if amount:
            parts.append(f"{amount}{name}")
    return "".join(parts) or "0s"


if __name__ == "__main__":
    assert parse_duration("10m") == timedelta(minutes=10)
    assert parse_duration("1h") == timedelta(hours=1)
    assert parse_duration("7d") == timedelta(days=7)
    assert parse_duration("30s") == timedelta(seconds=30)
    assert parse_duration("2w") == timedelta(weeks=2)
    assert parse_duration("1h30m") == timedelta(hours=1, minutes=30)
    assert parse_duration("1H 30M") == timedelta(hours=1, minutes=30)

    for bad in ["", "10", "m", "10x", "abc", "10x5m", "-5m", "0m", "30d"]:
        try:
            parse_duration(bad)
        except ValueError as e:
            print(f"{bad!r:10} -> {e}")
        else:
            raise AssertionError(f"{bad!r} should have failed")

    assert format_duration(timedelta(hours=1, minutes=30)) == "1h30m"
    assert format_duration(timedelta(days=2, seconds=5)) == "2d5s"
    assert format_duration(timedelta(0)) == "0s"

    for s in ["10m", "1h", "7d", "1d2h3m4s"]:
        assert format_duration(parse_duration(s)) == s

    print("duration parser ok")
