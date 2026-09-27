# comprehensions
squares = []
for i in range(5):
    squares.append(i * i)
print(squares)

squares2 = [i * i for i in range(5)]
assert squares == squares2
assert squares2 == [0, 1, 4, 9, 16]

evens = [n for n in range(10) if n % 2 == 0]
assert evens == [0, 2, 4, 6, 8]

# conditional expression goes before for
labels = ["even" if n % 2 == 0 else "odd" for n in range(4)]
assert labels == ["even", "odd", "even", "odd"]

words = ["hello", "Python", "hi", "world"]
lengths = [len(w) for w in words]
assert lengths == [5, 6, 2, 5]

long_words = [w.upper() for w in words if len(w) > 2]
assert long_words == ["HELLO", "PYTHON", "WORLD"]

word_lengths = {w: len(w) for w in words}
print(word_lengths)
assert word_lengths["Python"] == 6

original = {"a": 1, "b": 2}
flipped = {v: k for k, v in original.items()}
assert flipped == {1: "a", 2: "b"}

first_letters = {w[0].lower() for w in words}
assert first_letters == {"h", "p", "w"}

# for clauses in nested-loop order
matrix = [[1, 2], [3, 4], [5, 6]]
flat = [num for row in matrix for num in row]
assert flat == [1, 2, 3, 4, 5, 6]

flat2 = []
for row in matrix:
    for num in row:
        flat2.append(num)
assert flat == flat2

grid = [[0 for _ in range(3)] for _ in range(2)]
assert grid == [[0, 0, 0], [0, 0, 0]]

total = sum(x * x for x in range(4))
assert total == 14

prices = {"apple": 1.2, "steak": 15.0, "bread": 2.5, "wine": 12.0}
cheap = {item: p for item, p in prices.items() if p < 5}
assert cheap == {"apple": 1.2, "bread": 2.5}

print("comprehensions ok")
