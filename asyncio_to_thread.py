# asyncio to_thread
import asyncio
import json
import tempfile
import time
from pathlib import Path


def write_report_blocking(path: Path, rows: list[dict]) -> int:
    time.sleep(0.2)
    text = json.dumps(rows, indent=2)
    path.write_text(text, encoding="utf-8")
    return len(text)


def read_report_blocking(path: Path) -> list[dict]:
    time.sleep(0.05)
    return json.loads(path.read_text(encoding="utf-8"))


async def heartbeat(stop: asyncio.Event, beats: list[float]) -> None:
    # stalls if the loop is blocked
    while not stop.is_set():
        beats.append(time.perf_counter())
        await asyncio.sleep(0.02)


async def run_with_heartbeat(use_thread: bool, path: Path, rows: list[dict]) -> int:
    stop = asyncio.Event()
    beats: list[float] = []
    hb = asyncio.create_task(heartbeat(stop, beats))
    await asyncio.sleep(0)

    if use_thread:
        await asyncio.to_thread(write_report_blocking, path, rows)
    else:
        write_report_blocking(path, rows)  # blocks the event loop

    stop.set()
    await hb
    return len(beats)


async def main() -> None:
    rows = [{"id": i, "name": f"user{i}"} for i in range(1000)]

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "report.json"

        blocked_beats = await run_with_heartbeat(False, path, rows)
        threaded_beats = await run_with_heartbeat(True, path, rows)
        print(f"heartbeats while blocking: {blocked_beats}, with to_thread: {threaded_beats}")
        assert blocked_beats <= 2
        assert threaded_beats >= 5

        size = await asyncio.to_thread(write_report_blocking, path, rows[:3])
        assert size == len(path.read_text())

        try:
            await asyncio.to_thread(read_report_blocking, Path(tmp) / "missing.json")
        except FileNotFoundError:
            print("error propagated from the thread")

        paths = [Path(tmp) / f"part{i}.json" for i in range(3)]
        start = time.perf_counter()
        await asyncio.gather(*(asyncio.to_thread(write_report_blocking, p, rows[:10]) for p in paths))
        elapsed = time.perf_counter() - start
        print(f"3 writes in parallel: {elapsed:.2f}s")
        assert elapsed < 0.5  # parallel: ~0.2s, not 0.6s

        loaded = await asyncio.to_thread(read_report_blocking, paths[0])
        assert loaded == rows[:10]

    print("to_thread ok")


if __name__ == "__main__":
    asyncio.run(main())
