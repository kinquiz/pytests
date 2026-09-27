# async sqlite soft delete
import asyncio
import time

import aiosqlite

SCHEMA = """
CREATE TABLE notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    body       TEXT    NOT NULL,
    created_at INTEGER NOT NULL,
    deleted_at INTEGER
);
CREATE INDEX idx_notes_deleted_at ON notes (deleted_at);
"""


async def add_note(db: aiosqlite.Connection, user_id: int, body: str, now: int | None = None) -> int:
    cur = await db.execute(
        "INSERT INTO notes (user_id, body, created_at) VALUES (?, ?, ?)",
        (user_id, body, now if now is not None else int(time.time())),
    )
    await db.commit()
    return cur.lastrowid


async def list_notes(db: aiosqlite.Connection, user_id: int, include_deleted: bool = False) -> list[aiosqlite.Row]:
    sql = "SELECT * FROM notes WHERE user_id = ?"
    if not include_deleted:
        sql += " AND deleted_at IS NULL"
    async with db.execute(sql + " ORDER BY id", (user_id,)) as cur:
        return list(await cur.fetchall())


async def soft_delete(db: aiosqlite.Connection, note_id: int, now: int | None = None) -> bool:
    # don't bump timestamp on repeat delete
    cur = await db.execute(
        "UPDATE notes SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL",
        (now if now is not None else int(time.time()), note_id),
    )
    await db.commit()
    return cur.rowcount == 1


async def restore(db: aiosqlite.Connection, note_id: int) -> bool:
    cur = await db.execute("UPDATE notes SET deleted_at = NULL WHERE id = ? AND deleted_at IS NOT NULL", (note_id,))
    await db.commit()
    return cur.rowcount == 1


async def purge_deleted_before(db: aiosqlite.Connection, cutoff: int) -> int:
    # never touches live rows
    cur = await db.execute("DELETE FROM notes WHERE deleted_at IS NOT NULL AND deleted_at < ?", (cutoff,))
    await db.commit()
    return cur.rowcount


async def main() -> None:
    DAY = 86_400
    now = 1_700_000_000

    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(SCHEMA)

        a = await add_note(db, 1, "first", now - 40 * DAY)
        b = await add_note(db, 1, "second", now - 20 * DAY)
        c = await add_note(db, 1, "third", now - 1 * DAY)
        d = await add_note(db, 1, "fourth", now)

        assert len(await list_notes(db, 1)) == 4

        assert await soft_delete(db, a, now - 35 * DAY)
        assert await soft_delete(db, b, now - 10 * DAY)
        assert await soft_delete(db, c, now - 1 * DAY)
        assert not await soft_delete(db, c, now)

        visible = await list_notes(db, 1)
        assert [r["body"] for r in visible] == ["fourth"]
        assert len(await list_notes(db, 1, include_deleted=True)) == 4

        assert await restore(db, c)
        assert not await restore(db, d)
        assert [r["body"] for r in await list_notes(db, 1)] == ["third", "fourth"]

        purged = await purge_deleted_before(db, now - 30 * DAY)
        assert purged == 1
        remaining = [r["body"] for r in await list_notes(db, 1, include_deleted=True)]
        assert remaining == ["second", "third", "fourth"]

        assert await purge_deleted_before(db, now + DAY) == 1
        assert [r["body"] for r in await list_notes(db, 1, include_deleted=True)] == ["third", "fourth"]

    print("soft delete ok")


if __name__ == "__main__":
    asyncio.run(main())
