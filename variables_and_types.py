# variables and types
name = "Alex"
age = 25
height = 1.78
is_student = True
nothing = None

print(name, age, height, is_student, nothing)
print(type(name))
print(type(age))
print(type(height))
print(type(is_student))
print(type(nothing))

assert type(name) == str
assert type(age) == int
assert type(height) == float
assert type(is_student) == bool
assert nothing is None

age_as_string = str(age)
print(age_as_string + " years")
assert age_as_string == "25"

number_from_text = int("42")
assert number_from_text == 42
assert float("3.5") == 3.5
assert int(3.99) == 3  # truncates, doesn't round

print(bool(0), bool(1), bool(""), bool("hi"), bool([]), bool([0]))
assert bool(0) == False
assert bool("") == False
assert bool([]) == False
assert bool([0]) == True

print(7 / 2)
print(7 // 2)
print(7 % 2)
print(2 ** 10)
assert 7 / 2 == 3.5
assert 7 // 2 == 3
assert 7 % 2 == 1
assert 2 ** 10 == 1024

print(0.1 + 0.2)
assert 0.1 + 0.2 != 0.3  # float precision
assert round(0.1 + 0.2, 2) == 0.3

x = y = z = 0
assert x == 0 and y == 0 and z == 0

a = 5
b = 10
a, b = b, a
assert a == 10
assert b == 5

assert isinstance(True, int)  # bool subclasses int
assert isinstance(age, (int, float))

big = 10 ** 30
print(big)  # no int overflow
assert big > 10 ** 29

print("all variable checks passed")
