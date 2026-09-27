# functions args kwargs lambda


def greet(name):
    return "Hello, " + name


assert greet("Ann") == "Hello, Ann"


def greet_with_default(name, greeting="Hi"):
    return f"{greeting}, {name}!"


assert greet_with_default("Bob") == "Hi, Bob!"
assert greet_with_default("Bob", "Hey") == "Hey, Bob!"
assert greet_with_default(greeting="Yo", name="Cat") == "Yo, Cat!"


def say_hi():
    print("hi")


assert say_hi() is None


def min_max(nums):
    return min(nums), max(nums)


lo, hi = min_max([4, 1, 9])
assert lo == 1 and hi == 9
assert min_max([4, 1, 9]) == (1, 9)


def add_all(*args):
    print("args is", args)
    total = 0
    for a in args:
        total += a
    return total


assert add_all() == 0
assert add_all(1, 2, 3) == 6

nums = [10, 20]
assert add_all(*nums) == 30


def make_profile(**kwargs):
    print("kwargs is", kwargs)
    return kwargs


profile = make_profile(name="Ann", age=30)
assert profile == {"name": "Ann", "age": 30}


def everything(a, b=2, *args, c=3, **kwargs):
    return a, b, args, c, kwargs


assert everything(1) == (1, 2, (), 3, {})
assert everything(1, 5, 6, 7, c=8, d=9) == (1, 5, (6, 7), 8, {"d": 9})

settings = {"c": 100, "extra": True}
assert everything(0, **settings) == (0, 2, (), 100, {"extra": True})


# mutable default is shared across calls
def add_item_bad(item, items=[]):
    items.append(item)
    return items


first = add_item_bad("a")
second = add_item_bad("b")
print(second)
assert second == ["a", "b"]


def add_item_good(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items


assert add_item_good("a") == ["a"]
assert add_item_good("b") == ["b"]


double = lambda x: x * 2
assert double(4) == 8

add = lambda a, b: a + b
assert add(2, 3) == 5

people = [("Ann", 30), ("Bob", 25), ("Cat", 35)]
by_age = sorted(people, key=lambda p: p[1])
assert by_age[0] == ("Bob", 25)

words = ["banana", "kiwi", "apple"]
assert sorted(words, key=lambda w: len(w)) == ["kiwi", "apple", "banana"]
assert sorted(words, key=len) == ["kiwi", "apple", "banana"]

nums = [1, 2, 3, 4, 5]
doubled = list(map(lambda n: n * 2, nums))
assert doubled == [2, 4, 6, 8, 10]
odds = list(filter(lambda n: n % 2 == 1, nums))
assert odds == [1, 3, 5]

longest = max(words, key=len)
assert longest == "banana"


def apply_twice(func, value):
    return func(func(value))


assert apply_twice(double, 3) == 12
assert apply_twice(lambda s: s + "!", "hey") == "hey!!"


def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)


assert factorial(5) == 120
assert factorial(0) == 1

print("functions ok")
