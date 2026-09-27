# decorators
import functools
import time


def shout(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result.upper()
    return wrapper


def hello(name):
    return f"hello {name}"


loud_hello = shout(hello)
assert loud_hello("ann") == "HELLO ANN"


@shout
def hello2(name):
    return f"hi {name}"


assert hello2("bob") == "HI BOB"
print(hello2.__name__)  # 'wrapper' - no functools.wraps


def count_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper


@count_calls
def add(a, b):
    return a + b


add(1, 2)
add(3, 4)
assert add.calls == 2
assert add.__name__ == "add"


def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed * 1000:.2f} ms")
        return result
    return wrapper


@timed
def slow_sum(n):
    return sum(range(n))


assert slow_sum(100_000) == 4999950000


# arguments need an extra layer
def repeat(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                results.append(func(*args, **kwargs))
            return results
        return wrapper
    return decorator


@repeat(3)
def roll():
    return "rolled"


assert roll() == ["rolled", "rolled", "rolled"]


def retry(attempts, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"attempt {attempt} failed: {e}")
                    last_error = e
            raise last_error
        return wrapper
    return decorator


call_log = []


@retry(attempts=3, exceptions=(ConnectionError,))
def flaky():
    call_log.append(1)
    if len(call_log) < 3:
        raise ConnectionError("not yet")
    return "finally worked"


assert flaky() == "finally worked"
assert len(call_log) == 3


# bottom decorator applied first
def bold(func):
    @functools.wraps(func)
    def wrapper():
        return "<b>" + func() + "</b>"
    return wrapper


def italic(func):
    @functools.wraps(func)
    def wrapper():
        return "<i>" + func() + "</i>"
    return wrapper


@bold
@italic
def text():
    return "hi"


assert text() == "<b><i>hi</i></b>"


@functools.lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


assert fib(80) == 23416728348467685  # exponential without the cache

if __name__ == "__main__":
    print("decorators ok")
