# generators and iterators
import itertools


def count_up_to(n):
    i = 1
    while i <= n:
        yield i
        i += 1


gen = count_up_to(3)
print(gen)  # lazy, nothing has run yet
assert next(gen) == 1
assert next(gen) == 2
assert next(gen) == 3
try:
    next(gen)
except StopIteration:
    print("generator is used up")

assert list(count_up_to(5)) == [1, 2, 3, 4, 5]

g = count_up_to(2)
assert list(g) == [1, 2]
assert list(g) == []  # exhausted after one pass


# infinite - never list() it directly
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


first_ten = list(itertools.islice(fibonacci(), 10))
assert first_ten == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


def read_big_numbers(limit):
    for n in range(limit):
        yield n * n


total = sum(read_big_numbers(1_000_000))
assert total == 333332833333500000


def lines():
    yield "  apple  "
    yield ""
    yield "BANANA"
    yield "  "
    yield "cherry"


def stripped(items):
    for item in items:
        yield item.strip()


def non_empty(items):
    for item in items:
        if item:
            yield item


def lowered(items):
    for item in items:
        yield item.lower()


assert list(lowered(non_empty(stripped(lines())))) == ["apple", "banana", "cherry"]


def chain_all(*iterables):
    for it in iterables:
        yield from it


assert list(chain_all([1, 2], (3,), range(4, 6))) == [1, 2, 3, 4, 5]


class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


assert list(Countdown(3)) == [3, 2, 1]


it = iter(["a", "b"])
assert next(it) == "a"
assert next(it) == "b"
assert next(it, "default") == "default"


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


assert list(chunked([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]

assert list(itertools.chain([1], [2, 3])) == [1, 2, 3]
assert list(itertools.accumulate([1, 2, 3, 4])) == [1, 3, 6, 10]
assert list(itertools.batched("abcde", 2)) == [("a", "b"), ("c", "d"), ("e",)]  # 3.12+
pairs = list(itertools.combinations("abc", 2))
assert pairs == [("a", "b"), ("a", "c"), ("b", "c")]

if __name__ == "__main__":
    print("generators ok")
