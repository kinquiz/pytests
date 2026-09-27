# type hints and dataclasses
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Literal


def greet(name: str, times: int = 1) -> str:
    return " ".join([f"hi {name}"] * times)


def find_user(users: dict[int, str], user_id: int) -> str | None:
    # 3.10+ union syntax
    return users.get(user_id)


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


assert greet("ann", 2) == "hi ann hi ann"
assert find_user({1: "ann"}, 1) == "ann"
assert find_user({1: "ann"}, 2) is None
assert average([]) is None
assert average([1, 2, 3]) == 2

# hints aren't enforced at runtime
assert greet(123) == "hi 123"  # type: ignore[arg-type]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ModWarning:
    user_id: int
    moderator_id: int
    reason: str = "no reason given"
    created_at: datetime = field(default_factory=utc_now)
    # mutable defaults need default_factory
    tags: list[str] = field(default_factory=list)


w = ModWarning(user_id=1, moderator_id=2)
print(w)
assert w.reason == "no reason given"
assert w.tags == []
w.tags.append("spam")
assert ModWarning(1, 2).tags == []

fixed = datetime(2024, 1, 1, tzinfo=timezone.utc)
assert ModWarning(1, 2, "x", fixed) == ModWarning(1, 2, "x", fixed)


@dataclass(frozen=True, slots=True)
class GuildConfig:
    guild_id: int
    prefix: str = "!"
    log_channel_id: int | None = None
    mode: Literal["strict", "relaxed"] = "relaxed"


cfg = GuildConfig(guild_id=123)
try:
    cfg.prefix = "?"  # type: ignore[misc]
except AttributeError:  # FrozenInstanceError subclasses it
    print("frozen dataclass can't be changed")

strict = replace(cfg, mode="strict", log_channel_id=999)
assert strict.mode == "strict"
assert cfg.mode == "relaxed"
assert asdict(strict) == {"guild_id": 123, "prefix": "!", "log_channel_id": 999, "mode": "strict"}

# frozen -> hashable
assert len({cfg, GuildConfig(guild_id=123)}) == 1


@dataclass(order=True)
class Version:
    major: int
    minor: int = 0
    patch: int = 0

    @classmethod
    def parse(cls, text: str) -> "Version":
        parts = [int(p) for p in text.split(".")]
        return cls(*parts)


assert Version.parse("1.10.0") > Version.parse("1.9.3")  # tuple comparison, not string
assert sorted([Version(2), Version(1, 5), Version(1)]) == [Version(1), Version(1, 5), Version(2)]


@dataclass
class Percentage:
    value: float

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"percentage out of range: {self.value}")


try:
    Percentage(150)
except ValueError as e:
    print(e)

if __name__ == "__main__":
    print("type hints and dataclasses ok")
