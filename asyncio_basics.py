# asyncio basics
import asyncio
import time


async def fetch_user(user_id: int, delay: float) -> dict:
    await asyncio.sleep(delay)
    return {"id": user_id, "name": f"user{user_id}"}


async def sequential() -> tuple[list[dict], float]:
    start = time.perf_counter()
    results = [await fetch_user(1, 0.1), await fetch_user(2, 0.1), await fetch_user(3, 0.1)]
    return results, time.perf_counter() - start


async def concurrent() -> tuple[list[dict], float]:
    start = time.perf_counter()
    results = await asyncio.gather(fetch_user(1, 0.1), fetch_user(2, 0.1), fetch_user(3, 0.1))
    return list(results), time.perf_counter() - start


async def might_fail(n: int) -> int:
    await asyncio.sleep(0.01)
    if n == 2:
        raise ValueError("2 is unlucky")
    return n * 10


async def main() -> None:
    # calling doesn't run it
    coro = fetch_user(0, 0)
    assert asyncio.iscoroutine(coro)
    await coro  # avoid 'never awaited' warning

    seq_results, seq_time = await sequential()
    con_results, con_time = await concurrent()
    print(f"sequential: {seq_time:.2f}s, concurrent: {con_time:.2f}s")
    assert seq_results == con_results
    assert seq_time >= 0.3
    assert con_time < 0.25

    # argument order, not finish order
    ordered = await asyncio.gather(fetch_user(1, 0.05), fetch_user(2, 0.0))
    assert [u["id"] for u in ordered] == [1, 2]

    # errors returned as values
    mixed = await asyncio.gather(*(might_fail(n) for n in range(4)), return_exceptions=True)
    assert mixed[0] == 0 and mixed[1] == 10 and mixed[3] == 30
    assert isinstance(mixed[2], ValueError)

    try:
        await asyncio.gather(might_fail(1), might_fail(2))
    except ValueError as e:
        print("gather raised:", e)

    task = asyncio.create_task(fetch_user(9, 0.05))
    await asyncio.sleep(0)  # yield so the task can start
    assert not task.done()
    user = await task
    assert user["id"] == 9 and task.done()

    try:
        async with asyncio.timeout(0.05):
            await fetch_user(1, 1.0)
    except TimeoutError:
        print("timed out as expected")

    assert await asyncio.wait_for(fetch_user(5, 0.01), timeout=1) == {"id": 5, "name": "user5"}

    # 3.11+, cancels siblings on failure
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch_user(1, 0.01))
        t2 = tg.create_task(fetch_user(2, 0.01))
    assert t1.result()["id"] == 1 and t2.result()["id"] == 2

    print("asyncio basics ok")


if __name__ == "__main__":
    asyncio.run(main())
