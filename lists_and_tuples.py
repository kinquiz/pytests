# lists and tuples
fruits = ["apple", "banana", "cherry"]
print(fruits)

fruits.append("date")
assert fruits == ["apple", "banana", "cherry", "date"]

fruits.insert(0, "avocado")
assert fruits[0] == "avocado"

removed = fruits.pop()
assert removed == "date"
assert len(fruits) == 4

fruits.remove("banana")
assert "banana" not in fruits
print(fruits)

assert fruits.index("cherry") == 2

nums = [1, 2, 3, 4, 5, 6]
assert nums[1:4] == [2, 3, 4]
assert nums[-2:] == [5, 6]
assert nums[::-1] == [6, 5, 4, 3, 2, 1]

unsorted = [3, 1, 2]
new_list = sorted(unsorted)
assert unsorted == [3, 1, 2]
assert new_list == [1, 2, 3]
unsorted.sort()
assert unsorted == [1, 2, 3]
result = unsorted.sort()
assert result is None  # sort() returns None

a = [1, 2]
a.append([3, 4])
assert a == [1, 2, [3, 4]]
b = [1, 2]
b.extend([3, 4])
assert b == [1, 2, 3, 4]

original = [1, 2, 3]
not_a_copy = original
not_a_copy.append(4)
print(original)  # alias, not a copy
assert original == [1, 2, 3, 4]

real_copy = original.copy()
real_copy.append(5)
assert original == [1, 2, 3, 4]
assert real_copy == [1, 2, 3, 4, 5]

scores = [70, 85, 90, 65]
assert sum(scores) == 310
assert min(scores) == 65
assert max(scores) == 90
average = sum(scores) / len(scores)
assert average == 77.5

grid = [[1, 2, 3], [4, 5, 6]]
assert grid[1][2] == 6

point = (3, 4)
print(point[0], point[1])
assert point[0] == 3

single = (5,)  # comma makes the tuple
not_a_tuple = (5)
assert type(single) == tuple
assert type(not_a_tuple) == int

x, y = point
assert x == 3 and y == 4

colors = ("red", "green", "blue", "green")
assert colors.count("green") == 2
assert colors.index("blue") == 2

distances = {(0, 0): "origin", (1, 0): "right"}
assert distances[(0, 0)] == "origin"

people = [("Ann", 30), ("Bob", 25)]
for person in people:
    print(person[0], "is", person[1])

print("lists and tuples ok")
