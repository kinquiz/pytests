# pytest parametrize and classes
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from custom_middleware_ip_allowlist import IPAllowlistMiddleware
from discord_test_helpers_and_mocks import make_guild, make_member
from discord_role_hierarchy_check import can_moderate
from fastapi_router_and_depends import User
from login_rate_limiting import FakeClock, LoginRateLimiter
from regex_duration_parser import parse_duration


class TestParseDuration:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("30s", timedelta(seconds=30)),
            ("10m", timedelta(minutes=10)),
            ("1h", timedelta(hours=1)),
            ("7d", timedelta(days=7)),
            ("2w", timedelta(weeks=2)),
            ("1h30m", timedelta(minutes=90)),
            (" 1D 2H ", timedelta(days=1, hours=2)),
        ],
    )
    def test_valid(self, text, expected):
        assert parse_duration(text) == expected

    @pytest.mark.parametrize("text", ["", "10", "h", "5x", "10x5m", "-1m", "0s", "5w"])
    def test_invalid(self, text):
        with pytest.raises(ValueError):
            parse_duration(text)


class TestIpAllowlist:
    @pytest.mark.parametrize(
        ("allowed", "ip", "expected"),
        [
            (["127.0.0.1"], "127.0.0.1", True),
            (["10.0.0.0/8"], "10.255.0.1", True),
            (["10.0.0.0/8"], "11.0.0.1", False),
            (["192.168.1.0/24", "::1"], "::1", True),
            (["127.0.0.1"], "::ffff:127.0.0.1", True),
            (["0.0.0.0/0"], "not-an-ip", False),
            (["0.0.0.0/0"], None, False),
            ([], "127.0.0.1", False),
        ],
        ids=lambda v: repr(v),
    )
    def test_is_allowed(self, allowed, ip, expected):
        assert IPAllowlistMiddleware(MagicMock(), allowed).is_allowed(ip) is expected


class TestLoginRateLimiter:
    @pytest.fixture(autouse=True)
    def _limiter(self):
        self.clock = FakeClock()
        self.limiter = LoginRateLimiter(max_attempts=3, window_seconds=60, clock=self.clock)

    def fail(self, ip: str = "1.2.3.4", times: int = 1) -> None:
        for _ in range(times):
            self.limiter.record_failure(ip)

    @pytest.mark.parametrize(("failures", "blocked"), [(0, False), (2, False), (3, True), (10, True)])
    def test_threshold(self, failures, blocked):
        self.fail(times=failures)
        assert self.limiter.is_blocked("1.2.3.4") is blocked

    @pytest.mark.parametrize(("elapsed", "blocked"), [(59, True), (61, False)])
    def test_window_expiry(self, elapsed, blocked):
        self.fail(times=3)
        self.clock.advance(elapsed)
        assert self.limiter.is_blocked("1.2.3.4") is blocked

    def test_reset(self):
        self.fail(times=3)
        self.limiter.reset("1.2.3.4")
        assert not self.limiter.is_blocked("1.2.3.4")


class TestCanModerate:
    OWNER, ADMIN, MOD, MEMBER = 1, 2, 3, 4
    POSITIONS = {OWNER: 1, ADMIN: 30, MOD: 20, MEMBER: 1}

    @pytest.fixture(autouse=True)
    def _members(self):
        guild = make_guild(owner_id=self.OWNER)
        self.members = {uid: make_member(uid, guild=guild, top_role_position=pos) for uid, pos in self.POSITIONS.items()}

    @pytest.mark.parametrize(
        ("actor", "target", "expected"),
        [
            (OWNER, ADMIN, True),
            (OWNER, MEMBER, True),
            (ADMIN, OWNER, False),
            (ADMIN, MOD, True),
            (MOD, ADMIN, False),
            (MOD, MEMBER, True),
            (MEMBER, MEMBER, False),
        ],
    )
    def test_matrix(self, actor, target, expected):
        assert can_moderate(self.members[actor], self.members[target]) is expected


class TestApiAccess:
    @pytest.mark.parametrize(("path", "status"), [("/", 200), ("/api/health", 200), ("/api/me", 200), ("/api/admin/stats", 403)])
    def test_regular_user(self, client, path, status):
        assert client.get(path).status_code == status

    @pytest.mark.parametrize("current_user", [User("root", is_admin=True)])
    def test_admin_user(self, client, current_user):
        # parametrize overrides the current_user fixture
        assert client.get("/api/admin/stats").json()["requested_by"] == "root"
