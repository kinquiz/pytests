# loops
for i in range(3):
    print("i is", i)

assert list(range(2, 10, 3)) == [2, 5, 8]
assert list(range(5, 0, -1)) == [5, 4, 3, 2, 1]

total = 0
for n in [1, 2, 3, 4]:
    total += n
assert total == 10

count = 0
while count < 5:
    count += 1
assert count == 5

numbers = [4, 7, -1, 8, -3]
first_negative = None
for n in numbers:
    if n < 0:
        first_negative = n
        break
assert first_negative == -1

evens = []
for n in range(10):
    if n % 2 != 0:
        continue
    evens.append(n)
assert evens == [0, 2, 4, 6, 8]

# else runs only if no break
def has_zero(items):
    for item in items:
        if item == 0:
            break
    else:
        return False
    return True

assert has_zero([1, 0, 2]) == True
assert has_zero([1, 2, 3]) == False

colors = ["red", "green", "blue"]
for i in range(len(colors)):
    print(i, colors[i])

for i, color in enumerate(colors):
    print(i, color)

names = ["Ann", "Bob"]
ages = [30, 25]
for name, age in zip(names, ages):
    print(name, age)

secret = 7
guesses = [3, 9, 7, 1]
attempts = 0
while True:
    guess = guesses[attempts]
    attempts += 1
    if guess == secret:
        print("got it in", attempts)
        break
    elif guess < secret:
        print(guess, "too low")
    else:
        print(guess, "too high")
assert attempts == 3

table = []
for row in range(1, 4):
    line = []
    for col in range(1, 4):
        line.append(row * col)
    table.append(line)
print(table)
assert table[2] == [3, 6, 9]

vowels = 0
for ch in "programming":
    if ch in "aeiou":
        vowels += 1
assert vowels == 3

out = []
for i in range(1, 16):
    if i % 15 == 0:
        out.append("FizzBuzz")
    elif i % 3 == 0:
        out.append("Fizz")
    elif i % 5 == 0:
        out.append("Buzz")
    else:
        out.append(str(i))
assert out[14] == "FizzBuzz"
assert out[2] == "Fizz"
assert out[4] == "Buzz"
print(", ".join(out))

print("loops ok")
