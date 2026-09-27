# asyncio event and lock
import asyncio


class Service:
    def __init__(self) -> None:
        self.ready = asyncio.Event()
        self.cache: dict[str, int] = {}

    async def start(self) -> None:
        await asyncio.sleep(0.05)
        self.cache = {"alpha": 1, "beta": 2}
        self.ready.set()

    async def lookup(self, key: str) -> int | None:
        await self.ready.wait()
        return self.cache.get(key)


class Counter:
    def __init__(self) -> None:
        self.value = 0
        self.lock = asyncio.Lock()

    async def unsafe_increment(self) -> None:
        # await between read and write -> lost updates
        current = self.value
        await asyncio.sleep(0)
        self.value = current + 1

    async def safe_increment(self) -> None:
        async with self.lock:
            current = self.value
            await asyncio.sleep(0)
            self.value = current + 1


class RateLimitedSender:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.sent: list[str] = []

    async def send(self, msg: str) -> None:
        async with self._lock:
            await asyncio.sleep(0.001)
            self.sent.append(msg)


async def main() -> None:
    svc = Service()
    assert not svc.ready.is_set()

    # started before ready, they wait
    lookups = [asyncio.create_task(svc.lookup(k)) for k in ("alpha", "beta", "gamma")]
    await asyncio.sleep(0.01)
    assert not any(t.done() for t in lookups)

    await svc.start()
    assert await asyncio.gather(*lookups) == [1, 2, None]
    assert await svc.lookup("alpha") == 1

    never = asyncio.Event()
    try:
        await asyncio.wait_for(never.wait(), timeout=0.02)
    except TimeoutError:
        print("event never got set, timed out")

    c = Counter()
    await asyncio.gather(*(c.unsafe_increment() for _ in range(100)))
    print("without lock:", c.value)
    assert c.value < 100

    c2 = Counter()
    await asyncio.gather(*(c2.safe_increment() for _ in range(100)))
    print("with lock:", c2.value)
    assert c2.value == 100

    assert not c2.lock.locked()

    sender = RateLimitedSender()
    await asyncio.gather(*(sender.send(f"msg{i}") for i in range(5)))
    assert sender.sent == [f"msg{i}" for i in range(5)]  # asyncio.Lock is FIFO

    print("event and lock ok")


if __name__ == "__main__":
    asyncio.run(main())
