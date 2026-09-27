# tests for mini project
import logging
from unittest.mock import MagicMock

import discord
import pytest

from conftest_and_shared_fixtures import AUDIT_CHANNEL_ID
from custom_exceptions import PermissionDenied
from discord_test_helpers_and_mocks import make_guild, make_http_response, make_member
from putting_it_together_mini_project import (
    Action,
    ModerationDB,
    ModerationService,
    build_audit_embed,
    get_db_path,
)

GUILD = 1000
NOW = 1_700_000_000
DAY = 86_400


async def test_db_uses_temp_file(db, db_path):
    assert get_db_path() == db_path
    assert db.path == db_path
    assert db_path.exists()


async def test_record_and_get(db):
    entry = await db.record(GUILD, 2, 3, Action.WARN, "spam", now=NOW)
    fetched = await db.get(entry.id)
    assert fetched == entry
    assert fetched.action is Action.WARN
    assert await db.get(999) is None


async def test_list_filters_and_order(db):
    await db.record(GUILD, 2, 3, Action.WARN, "a")
    await db.record(GUILD, 2, 4, Action.KICK, "b")
    await db.record(GUILD, 2, 3, Action.BAN, "c")
    await db.record(GUILD + 1, 2, 3, Action.WARN, "other guild")

    assert [e.reason for e in await db.list_entries(GUILD)] == ["c", "b", "a"]
    assert [e.reason for e in await db.list_entries(GUILD, target_id=3)] == ["c", "a"]
    assert [e.reason for e in await db.list_entries(GUILD, action=Action.KICK)] == ["b"]


async def test_pagination(db):
    for i in range(25):
        await db.record(GUILD, 2, 3, Action.WARN, str(i))
    page1 = await db.list_entries(GUILD, per_page=10)
    page3 = await db.list_entries(GUILD, per_page=10, page=3)
    assert [e.reason for e in page1] == [str(i) for i in range(24, 14, -1)]
    assert [e.reason for e in page3] == [str(i) for i in range(4, -1, -1)]


async def test_get_many_chunks(db):
    ids = [(await db.record(GUILD, 2, 3, Action.WARN)).id for _ in range(7)]
    got = await db.get_many([*ids, 12345], chunk_size=3)  # unknown id ignored
    assert [e.id for e in got] == ids


async def test_soft_delete_and_purge(db):
    old = await db.record(GUILD, 2, 3, Action.WARN, "old", now=NOW - 40 * DAY)
    recent = await db.record(GUILD, 2, 3, Action.WARN, "recent", now=NOW - DAY)
    live = await db.record(GUILD, 2, 3, Action.WARN, "live", now=NOW - 90 * DAY)

    assert await db.soft_delete(old.id, now=NOW - 35 * DAY)
    assert await db.soft_delete(recent.id, now=NOW - DAY)
    assert not await db.soft_delete(recent.id)  # idempotent

    assert [e.reason for e in await db.list_entries(GUILD)] == ["live"]
    assert len(await db.list_entries(GUILD, include_deleted=True)) == 3

    assert await db.purge_deleted_before(NOW - 30 * DAY) == 1
    remaining = await db.list_entries(GUILD, include_deleted=True)
    assert {e.reason for e in remaining} == {"recent", "live"}
    assert (await db.get(live.id)).is_deleted is False


async def test_unconnected_db_raises(db_path):
    with pytest.raises(RuntimeError, match="not connected"):
        await ModerationDB().get(1)


@pytest.fixture
def guild():
    return make_guild(guild_id=GUILD, owner_id=1)


@pytest.fixture
def mod(guild):
    return make_member(2, guild=guild, top_role_position=20)


@pytest.fixture
def target(guild):
    return make_member(3, guild=guild, top_role_position=1)


@pytest.mark.parametrize("action", list(Action))
async def test_moderate_records_without_channel(db, fake_bot, mod, target, action):
    service = ModerationService(db, fake_bot)
    result = await service.moderate(mod, target, action, "reason")

    assert result.announced is False
    stored = await db.get(result.entry.id)
    assert (stored.guild_id, stored.actor_id, stored.target_id, stored.action) == (GUILD, 2, 3, action)
    fake_bot.get_channel.assert_not_called()


async def test_moderate_posts_embed_when_channel_available(db, fake_bot, audit_channel, mod, target):
    service = ModerationService(db, fake_bot, audit_channel_id=AUDIT_CHANNEL_ID)
    result = await service.moderate(mod, target, Action.BAN, "raid")

    assert result.announced is True
    audit_channel.send.assert_awaited_once()
    embed = audit_channel.send.await_args.kwargs["embed"]
    assert embed.title == f"Ban · case #{result.entry.id}"
    assert {f.name: f.value for f in embed.fields}["Reason"] == "raid"


async def test_channel_missing_from_cache(db, fake_bot, audit_channel, mod, target):
    service = ModerationService(db, fake_bot, audit_channel_id=AUDIT_CHANNEL_ID + 1)
    assert (await service.moderate(mod, target, Action.WARN)).announced is False
    audit_channel.send.assert_not_awaited()


async def test_non_text_channel_is_ignored(db, fake_bot, mod, target):
    fake_bot.get_channel.return_value = MagicMock(spec=discord.VoiceChannel)
    service = ModerationService(db, fake_bot, audit_channel_id=AUDIT_CHANNEL_ID)
    assert (await service.moderate(mod, target, Action.WARN)).announced is False


async def test_send_failure_keeps_the_record(db, fake_bot, audit_channel, mod, target, caplog):
    audit_channel.send.side_effect = discord.Forbidden(make_http_response(403, "Forbidden"), "Missing Access")
    service = ModerationService(db, fake_bot, audit_channel_id=AUDIT_CHANNEL_ID)

    with caplog.at_level(logging.WARNING):
        result = await service.moderate(mod, target, Action.KICK)

    assert result.announced is False
    assert await db.get(result.entry.id) is not None
    assert "failed to post case" in caplog.text


async def test_refused_action_is_not_recorded(db, fake_bot, guild, target):
    low = make_member(5, guild=guild, top_role_position=1)
    service = ModerationService(db, fake_bot)

    with pytest.raises(PermissionDenied) as exc_info:
        await service.moderate(low, target, Action.BAN)

    assert exc_info.value.command_name == "ban"
    assert await db.list_entries(GUILD) == []


async def test_owner_cannot_be_targeted(db, fake_bot, guild, mod):
    owner = make_member(1, guild=guild, top_role_position=1)
    with pytest.raises(PermissionDenied):
        await ModerationService(db, fake_bot).moderate(mod, owner, Action.WARN)


def test_audit_embed_defaults():
    from putting_it_together_mini_project import AuditEntry

    embed = build_audit_embed(AuditEntry(7, GUILD, 2, 3, Action.TIMEOUT, "", NOW))
    assert embed.title == "Timeout · case #7"
    assert {f.name: f.value for f in embed.fields}["Reason"] == "—"
    assert embed.timestamp.timestamp() == NOW
