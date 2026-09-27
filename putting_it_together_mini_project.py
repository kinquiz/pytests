# putting it together mini project
from __future__ import annotations

import logging
import os
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Self

import aiosqlite
import discord

from async_sqlite_dynamic_queries import DEFAULT_CHUNK_SIZE, build_where_clause, chunked, paginate
from custom_exceptions import PermissionDenied
from discord_embeds_helpers import info_embed
from discord_role_hierarchy_check import can_moderate

log = logging.getLogger(__name__)

DB_PATH_ENV = "PRACTICE_DB_PATH"
DEFAULT_DB_PATH = "practice.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id   INTEGER NOT NULL,
    actor_id   INTEGER NOT NULL,
    target_id  INTEGER NOT NULL,
    action     TEXT    NOT NULL,
    reason     TEXT    NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL,
    deleted_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_audit_guild_target ON audit_log (guild_id, target_id);
CREATE INDEX IF NOT EXISTS idx_audit_deleted_at ON audit_log (deleted_at);
"""

_FILTERABLE = {"guild_id", "target_id", "actor_id", "action"}


def get_db_path() -> Path:
    return Path(os.environ.get(DB_PATH_ENV, DEFAULT_DB_PATH))


class Action(StrEnum):
    WARN = "warn"
    TIMEOUT = "timeout"
    KICK = "kick"
    BAN = "ban"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    id: int
    guild_id: int
    actor_id: int
    target_id: int
    action: Action
    reason: str
    created_at: int
    deleted_at: int | None = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> Self:
        return cls(**{**dict(row), "action": Action(row["action"])})

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class ModerationDB:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else get_db_path()
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.executescript(SCHEMA)
        await conn.commit()
        self._conn = conn

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("ModerationDB is not connected")
        return self._conn

    async def record(
        self,
        guild_id: int,
        actor_id: int,
        target_id: int,
        action: Action,
        reason: str = "",
        *,
        now: int | None = None,
    ) -> AuditEntry:
        created_at = int(time.time()) if now is None else now
        cur = await self.conn.execute(
            "INSERT INTO audit_log (guild_id, actor_id, target_id, action, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, actor_id, target_id, str(action), reason, created_at),
        )
        await self.conn.commit()
        return AuditEntry(cur.lastrowid, guild_id, actor_id, target_id, action, reason, created_at)

    async def get(self, entry_id: int) -> AuditEntry | None:
        async with self.conn.execute("SELECT * FROM audit_log WHERE id = ?", (entry_id,)) as cur:
            row = await cur.fetchone()
        return AuditEntry.from_row(row) if row else None

    async def list_entries(
        self,
        guild_id: int,
        *,
        target_id: int | None = None,
        action: Action | None = None,
        include_deleted: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> list[AuditEntry]:
        where, params = build_where_clause(
            {"guild_id": guild_id, "target_id": target_id, "action": str(action) if action else None},
            _FILTERABLE,
        )
        if not include_deleted:
            where += " AND deleted_at IS NULL"  # WHERE always present (guild_id required)
        limit, offset = paginate(page, per_page)
        sql = f"SELECT * FROM audit_log{where} ORDER BY id DESC LIMIT ? OFFSET ?"
        async with self.conn.execute(sql, [*params, limit, offset]) as cur:
            return [AuditEntry.from_row(r) for r in await cur.fetchall()]

    async def get_many(self, ids: Sequence[int], *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[AuditEntry]:
        out: list[AuditEntry] = []
        for chunk in chunked(ids, chunk_size):
            placeholders = ", ".join("?" * len(chunk))
            async with self.conn.execute(f"SELECT * FROM audit_log WHERE id IN ({placeholders})", list(chunk)) as cur:
                out.extend(AuditEntry.from_row(r) for r in await cur.fetchall())
        return sorted(out, key=lambda e: e.id)

    async def soft_delete(self, entry_id: int, *, now: int | None = None) -> bool:
        cur = await self.conn.execute(
            "UPDATE audit_log SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL",
            (int(time.time()) if now is None else now, entry_id),
        )
        await self.conn.commit()
        return cur.rowcount == 1

    async def purge_deleted_before(self, cutoff: int) -> int:
        cur = await self.conn.execute(
            "DELETE FROM audit_log WHERE deleted_at IS NOT NULL AND deleted_at < ?", (cutoff,)
        )
        await self.conn.commit()
        return cur.rowcount


def build_audit_embed(entry: AuditEntry) -> discord.Embed:
    embed = info_embed(
        f"{entry.action.title()} · case #{entry.id}",
        fields={
            "Moderator": f"<@{entry.actor_id}>",
            "Target": f"<@{entry.target_id}>",
            "Reason": entry.reason or "—",
        },
    )
    embed.timestamp = datetime.fromtimestamp(entry.created_at, tz=timezone.utc)
    return embed


@dataclass(frozen=True, slots=True)
class ModerationResult:
    entry: AuditEntry
    announced: bool


class ModerationService:
    def __init__(self, db: ModerationDB, bot: discord.Client, *, audit_channel_id: int | None = None) -> None:
        self.db = db
        self.bot = bot
        self.audit_channel_id = audit_channel_id

    async def moderate(
        self,
        actor: discord.Member,
        target: discord.Member,
        action: Action,
        reason: str = "",
    ) -> ModerationResult:
        if not can_moderate(actor, target):
            raise PermissionDenied(str(action), required="a higher role than the target")
        entry = await self.db.record(target.guild.id, actor.id, target.id, action, reason)
        announced = await self.post_audit_embed(entry)
        log.info("case #%d: %s by %s on %s (announced=%s)", entry.id, action, actor.id, target.id, announced)
        return ModerationResult(entry, announced)

    def _audit_channel(self) -> discord.TextChannel | None:
        if self.audit_channel_id is None:
            return None
        channel = self.bot.get_channel(self.audit_channel_id)
        # cache lookup: may be None or a non-text channel
        return channel if isinstance(channel, discord.TextChannel) else None

    async def post_audit_embed(self, entry: AuditEntry) -> bool:
        channel = self._audit_channel()
        if channel is None:
            log.debug("no audit channel available, case #%d not announced", entry.id)
            return False
        try:
            await channel.send(embed=build_audit_embed(entry))
        except discord.HTTPException:
            # action already recorded; don't fail on announce
            log.warning("failed to post case #%d to audit channel %s", entry.id, self.audit_channel_id, exc_info=True)
            return False
        return True
