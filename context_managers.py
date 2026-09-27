# context managers
import contextlib
import os
import tempfile
import time


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.elapsed = time.perf_counter() - self.start
        # falsy return re-raises
        return False


with Timer() as t:
    sum(range(10_000))
print(f"took {t.elapsed:.6f}s")
assert t.elapsed >= 0


events = []


class Tracked:
    def __enter__(self):
        events.append("enter")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        events.append(f"exit ({exc_type.__name__ if exc_type else 'no error'})")
        return False


try:
    with Tracked():
        raise RuntimeError("boom")
except RuntimeError:
    pass
assert events == ["enter", "exit (RuntimeError)"]


# True swallows the exception
class IgnoreZeroDivision:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return exc_type is ZeroDivisionError


with IgnoreZeroDivision():
    1 / 0
print("still running after 1/0")

with contextlib.suppress(FileNotFoundError):
    os.remove("definitely_not_here.txt")


@contextlib.contextmanager
def temporary_env(key, value):
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            del os.environ[key]
        else:
            os.environ[key] = old


assert "PRACTICE_FLAG" not in os.environ
with temporary_env("PRACTICE_FLAG", "on"):
    assert os.environ["PRACTICE_FLAG"] == "on"
assert "PRACTICE_FLAG" not in os.environ


@contextlib.contextmanager
def working_file(content):
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    with open(path, "w") as f:
        f.write(content)
    try:
        yield path
    finally:
        os.remove(path)


with working_file("hello") as path:
    with open(path) as f:
        assert f.read() == "hello"
    saved_path = path
assert not os.path.exists(saved_path)


with tempfile.TemporaryDirectory() as tmp:
    a_path = os.path.join(tmp, "a.txt")
    b_path = os.path.join(tmp, "b.txt")
    with open(a_path, "w") as a, open(b_path, "w") as b:
        a.write("A")
        b.write("B")
    assert sorted(os.listdir(tmp)) == ["a.txt", "b.txt"]


# ExitStack: dynamic number of contexts
with tempfile.TemporaryDirectory() as tmp:
    names = [os.path.join(tmp, f"{i}.txt") for i in range(3)]
    with contextlib.ExitStack() as stack:
        files = [stack.enter_context(open(n, "w")) for n in names]
        for i, f in enumerate(files):
            f.write(str(i))
    assert all(f.closed for f in files)

if __name__ == "__main__":
    print("context managers ok")
