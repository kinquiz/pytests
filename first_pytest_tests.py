# first pytest tests
from datetime import timedelta

import pytest

from custom_exceptions import PermissionDenied, handle, run_command
from ipaddress_module import is_allowed, parse_networks
from regex_duration_parser import format_duration, parse_duration


def test_parse_minutes():
    assert parse_duration("10m") == timedelta(minutes=10)


def test_parse_hours():
    assert parse_duration("1h") == timedelta(hours=1)


def test_parse_days():
    assert parse_duration("7d") == timedelta(days=7)


def test_parse_combined():
    assert parse_duration("1h30m") == timedelta(minutes=90)


def test_parse_rejects_garbage():
    with pytest.raises(ValueError):
        parse_duration("banana")


def test_parse_rejects_zero():
    with pytest.raises(ValueError, match="greater than zero"):
        parse_duration("0m")


def test_parse_rejects_too_long():
    with pytest.raises(ValueError, match="28 days"):
        parse_duration("29d")


def test_format_round_trip():
    assert format_duration(parse_duration("2d3h")) == "2d3h"


def test_permission_denied_carries_command_name():
    with pytest.raises(PermissionDenied) as exc_info:
        run_command(2, "admin_ban")
    assert exc_info.value.command_name == "admin_ban"
    assert exc_info.value.required == "admin"


def test_handle_turns_errors_into_messages():
    assert handle(2, "admin_ban") == "denied: admin_ban"
    assert handle(404, "ping").startswith("error:")


def test_allowlist_basic():
    nets = parse_networks("127.0.0.1, 10.0.0.0/8")
    assert is_allowed("127.0.0.1", nets)
    assert is_allowed("10.1.2.3", nets)
    assert not is_allowed("192.168.0.1", nets)


def test_empty_allowlist_blocks_everyone():
    assert not is_allowed("127.0.0.1", [])


def test_invalid_ip_is_not_allowed():
    assert not is_allowed("hello", parse_networks("0.0.0.0/0"))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
