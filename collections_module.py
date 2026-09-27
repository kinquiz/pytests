# collections module
from collections import Counter, OrderedDict, defaultdict, deque, namedtuple
from datetime import datetime, timezone

words = ["apple", "avocado", "banana", "blueberry", "cherry"]
by_letter = defaultdict(list)
for w in words:
    by_letter[w[0]].append(w)
assert by_letter["a"] == ["apple", "avocado"]
assert by_letter["z"] == []
assert "z" in by_letter  # lookup inserts the key

counts = defaultdict(int)
for ch in "mississippi":
    counts[ch] += 1
assert counts["s"] == 4

# guild -> user -> count
warnings = defaultdict(lambda: defaultdict(int))
warnings[111][42] += 1
warnings[111][42] += 1
warnings[222][7] += 1
assert warnings[111][42] == 2
assert dict(warnings[222]) == {7: 1}

c = Counter("mississippi")
assert c.most_common(1) == [("i", 4)] or c.most_common(1) == [("s", 4)]  # tie broken by insertion order
assert c["p"] == 2
assert c["z"] == 0

q = deque([1, 2, 3])
q.appendleft(0)
q.append(4)
assert list(q) == [0, 1, 2, 3, 4]
assert q.popleft() == 0  # O(1), unlike list.pop(0)
q.rotate(1)
assert list(q) == [4, 1, 2, 3]


# maxlen drops oldest entries automatically
class RecentEvents:
    def __init__(self, limit: int = 5):
        self._events = deque(maxlen=limit)

    def record(self, kind: str, detail: str) -> None:
        self._events.append((datetime.now(timezone.utc), kind, detail))

    def latest(self, n: int | None = None) -> list[tuple]:
        items = list(reversed(self._events))
        return items if n is None else items[:n]

    def __len__(self) -> int:
        return len(self._events)


log = RecentEvents(limit=3)
for i in range(5):
    log.record("join", f"user{i}")
assert len(log) == 3
details = [detail for _, _, detail in log.latest()]
assert details == ["user4", "user3", "user2"]
assert [d for _, _, d in log.latest(1)] == ["user4"]

Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
assert p.x == 3 and p[1] == 4
assert p._replace(x=10) == Point(10, 4)
assert p._asdict() == {"x": 3, "y": 4}

# move_to_end still useful for LRU
od = OrderedDict(a=1, b=2, c=3)
od.move_to_end("a")
assert list(od) == ["b", "c", "a"]
od.popitem(last=False)
assert list(od) == ["c", "a"]

if __name__ == "__main__":
    for ts, kind, detail in log.latest():
        print(ts.strftime("%H:%M:%S"), kind, detail)
    print("collections ok")
