# conditionals


def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    else:
        return "F"


print(grade(95), grade(85), grade(72), grade(10))
assert grade(95) == "A"
assert grade(90) == "A"
assert grade(89) == "B"
assert grade(70) == "C"
assert grade(0) == "F"

age = 20
has_ticket = True
if age >= 18 and has_ticket:
    can_enter = True
else:
    can_enter = False
assert can_enter

is_weekend = False
is_holiday = True
day_off = is_weekend or is_holiday
assert day_off

assert not False

x = 5
assert 1 < x < 10
assert not (10 < x < 20)

status = "adult" if age >= 18 else "minor"
assert status == "adult"

name = ""
if name:
    greeting = "Hello " + name
else:
    greeting = "Hello stranger"
assert greeting == "Hello stranger"

items = []
if not items:
    print("list is empty")

value = None
if value is None:
    value = "default"
assert value == "default"


# 400 beats 100 beats 4
def is_leap(year):
    if year % 400 == 0:
        return True
    elif year % 100 == 0:
        return False
    elif year % 4 == 0:
        return True
    else:
        return False


assert is_leap(2000) == True
assert is_leap(1900) == False
assert is_leap(2024) == True
assert is_leap(2023) == False

command = "quit"
if command == "quit" or command == "exit" or command == "q":
    should_quit = True
assert should_quit
if command in ("quit", "exit", "q"):
    should_quit2 = True
assert should_quit2

# 3.10+
def describe(thing):
    match thing:
        case 0:
            return "zero"
        case int() if thing < 0:
            return "negative int"
        case int():
            return "positive int"
        case str():
            return "a string"
        case [first, *rest]:
            return f"list starting with {first}"
        case _:
            return "something else"


assert describe(0) == "zero"
assert describe(-5) == "negative int"
assert describe(3) == "positive int"
assert describe("hey") == "a string"
assert describe([9, 8, 7]) == "list starting with 9"
assert describe(2.5) == "something else"

print("conditionals ok")
