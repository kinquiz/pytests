# async sqlite dynamic queries
import asyncio
from collections.abc import Iterator, Sequence
from typing import Any, TypeVar

import aiosqlite

T = TypeVar("T")

# old sqlite limit: 999 bound vars
SQLITE_MAX_VARS = 999
DEFAULT_CHUNK_SIZE = 900


def build_where_clause(filters: dict[str, Any], allowed_columns: set[str]) -> tuple[str, list[Any]]:
    # only allowlisted column names reach the SQL
    clauses: list[str] = []
    params: list[Any] = []
    for column, value in filters.items():
        if value is None:
            continue
        if column not in allowed_columns:
            raise ValueError(f"cannot filter on {column!r}")
        if isinstance(value, (list, tuple, set)):
            if not value:
                # IN () is invalid; match nothing
                clauses.append("0")
                continue
            clauses.append(f"{column} IN ({', '.join('?' * len(value))})")
            params.extend(value)
        else:
            clauses.append(f"{column} = ?")
            params.append(value)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


def paginate(page: int, per_page: int, max_per_page: int = 100) -> tuple[int, int]:
    # page is 1-based
    if page < 1:
        raise ValueError("page starts at 1")
    per_page = max(1, min(per_page, max_per_page))
    return per_page, (page - 1) * per_page


def chunked(items: Sequence[T], size: int = DEFAULT_CHUNK_SIZE) -> Iterator[Sequence[T]]:
    if size < 1:
        raise ValueError("chunk size must be positive")
    for start in range(0, len(items), size):
        yield items[start:start + size]


async def search_members(
    db: aiosqlite.Connection,
    *,
    guild_id: int | None = None,
    role: str | None = None,
    is_bot: bool | None = None,
    page: int = 1,
    per_page: int = 20,
) -> list[aiosqlite.Row]:
    where, params = build_where_clause(
        {"guild_id": guild_id, "role": role, "is_bot": is_bot},
        allowed_columns={"guild_id", "role", "is_bot"},
    )
    limit, offset = paginate(page, per_page)
    sql = f"SELECT * FROM members{where} ORDER BY user_id LIMIT ? OFFSET ?"
    async with db.execute(sql, [*params, limit, offset]) as cur:
        return list(await cur.fetchall())


async def fetch_by_ids(db: aiosqlite.Connection, user_ids: Sequence[int], chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[aiosqlite.Row]:
    results: list[aiosqlite.Row] = []
    for chunk in chunked(user_ids, chunk_size):
        placeholders = ", ".join("?" * len(chunk))
        async with db.execute(f"SELECT * FROM members WHERE user_id IN ({placeholders})", list(chunk)) as cur:
            results.extend(await cur.fetchall())
    return results


async def seed(db: aiosqlite.Connection, n: int) -> None:
    await db.execute(
        "CREATE TABLE members (user_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, role TEXT NOT NULL, is_bot INTEGER NOT NULL)"
    )
    rows = [(i, 1 if i % 2 else 2, "mod" if i % 10 == 0 else "member", int(i % 50 == 0)) for i in range(1, n + 1)]
    await db.executemany("INSERT INTO members VALUES (?, ?, ?, ?)", rows)
    await db.commit()


async def main() -> None:
    where, params = build_where_clause({"guild_id": 1, "role": None, "is_bot": False}, {"guild_id", "role", "is_bot"})
    assert where == " WHERE guild_id = ? AND is_bot = ?"
    assert params == [1, False]
    assert build_where_clause({}, set()) == ("", [])
    assert build_where_clause({"role": ["a", "b"]}, {"role"}) == (" WHERE role IN (?, ?)", ["a", "b"])
    try:
        build_where_clause({"1=1; DROP TABLE members; --": 1}, {"role"})
    except ValueError as e:
        print("rejected:", e)

    assert paginate(1, 20) == (20, 0)
    assert paginate(3, 20) == (20, 40)
    assert paginate(1, 10_000) == (100, 0)

    assert [list(c) for c in chunked([1, 2, 3, 4, 5], 2)] == [[1, 2], [3, 4], [5]]
    assert list(chunked([], 3)) == []

    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await seed(db, 5000)

        page1 = await search_members(db, guild_id=2, role="mod", per_page=5)
        page2 = await search_members(db, guild_id=2, role="mod", per_page=5, page=2)
        assert [r["user_id"] for r in page1] == [10, 20, 30, 40, 50]
        assert [r["user_id"] for r in page2] == [60, 70, 80, 90, 100]

        bots = await search_members(db, is_bot=True, per_page=100)
        assert all(r["is_bot"] == 1 for r in bots) and len(bots) == 100

        everyone_first_page = await search_members(db)
        assert len(everyone_first_page) == 20

        ids = list(range(2, 5001, 2))
        assert len(ids) > SQLITE_MAX_VARS
        rows = await fetch_by_ids(db, ids)
        assert len(rows) == len(ids)
        assert {r["user_id"] for r in rows} == set(ids)

        assert await fetch_by_ids(db, [999_999]) == []
        assert await fetch_by_ids(db, []) == []

    print("dynamic queries ok")


if __name__ == "__main__":
    asyncio.run(main())
