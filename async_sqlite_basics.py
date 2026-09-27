# async sqlite basics
import asyncio

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS warnings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id     INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    reason       TEXT    NOT NULL DEFAULT '',
    created_at   INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_warnings_guild_user ON warnings (guild_id, user_id);
"""


async def init_db(db: aiosqlite.Connection) -> None:
    await db.executescript(SCHEMA)
    await db.commit()


async def add_warning(db: aiosqlite.Connection, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
    cursor = await db.execute(
        "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
        (guild_id, user_id, moderator_id, reason),
    )
    await db.commit()
    return cursor.lastrowid


async def get_warnings(db: aiosqlite.Connection, guild_id: int, user_id: int) -> list[aiosqlite.Row]:
    async with db.execute(
        "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY id",
        (guild_id, user_id),
    ) as cursor:
        return list(await cursor.fetchall())


async def count_warnings(db: aiosqlite.Connection, guild_id: int, user_id: int) -> int:
    async with db.execute(
        "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
    ) as cursor:
        (count,) = await cursor.fetchone()
    return count


async def update_reason(db: aiosqlite.Connection, warning_id: int, reason: str) -> bool:
    cursor = await db.execute("UPDATE warnings SET reason = ? WHERE id = ?", (reason, warning_id))
    await db.commit()
    return cursor.rowcount == 1


async def delete_warning(db: aiosqlite.Connection, warning_id: int) -> bool:
    cursor = await db.execute("DELETE FROM warnings WHERE id = ?", (warning_id,))  # 1-tuple
    await db.commit()
    return cursor.rowcount == 1


async def main() -> None:
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await init_db(db)

        GUILD, ANN, BOB, MOD = 100, 1, 2, 99

        first = await add_warning(db, GUILD, ANN, MOD, "spam")
        await add_warning(db, GUILD, ANN, MOD, "caps")
        await add_warning(db, GUILD, BOB, MOD, "off-topic")
        await add_warning(db, 200, ANN, MOD, "different server")
        assert first == 1

        rows = await get_warnings(db, GUILD, ANN)
        assert [r["reason"] for r in rows] == ["spam", "caps"]
        assert rows[0]["created_at"] > 0
        assert await count_warnings(db, GUILD, ANN) == 2
        assert await count_warnings(db, GUILD, 12345) == 0

        assert await update_reason(db, first, "spam (links)")
        assert not await update_reason(db, 9999, "nope")
        rows = await get_warnings(db, GUILD, ANN)
        assert rows[0]["reason"] == "spam (links)"

        assert await delete_warning(db, first)
        assert not await delete_warning(db, first)
        assert await count_warnings(db, GUILD, ANN) == 1

        # placeholders make injection inert
        evil = "x'; DROP TABLE warnings; --"
        await add_warning(db, GUILD, BOB, MOD, evil)
        rows = await get_warnings(db, GUILD, BOB)
        assert rows[-1]["reason"] == evil
        assert await count_warnings(db, GUILD, BOB) == 2

        try:
            await db.execute("INSERT INTO warnings (guild_id, user_id, moderator_id) VALUES (?, ?, ?)", (GUILD, 5, MOD))
            await db.execute("INSERT INTO warnings (guild_id, user_id, moderator_id) VALUES (?, ?, ?)", (GUILD, 5, None))
            await db.commit()
        except aiosqlite.IntegrityError as e:
            print("integrity error:", e)
            await db.rollback()
        assert await count_warnings(db, GUILD, 5) == 0  # first insert rolled back too

        await db.executemany(
            "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
            [(GUILD, 7, MOD, f"bulk {i}") for i in range(5)],
        )
        await db.commit()
        assert await count_warnings(db, GUILD, 7) == 5

    print("async sqlite basics ok")


if __name__ == "__main__":
    asyncio.run(main())
