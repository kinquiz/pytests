# strings
s = "Hello, World"

print(s.upper())
print(s.lower())
print(len(s))
assert s.upper() == "HELLO, WORLD"
assert s.lower() == "hello, world"
assert len(s) == 12

print(s[0])
print(s[-1])
print(s[0:5])
print(s[7:])
print(s[::-1])
assert s[0] == "H"
assert s[-1] == "d"
assert s[0:5] == "Hello"
assert s[7:] == "World"
assert s[::-1] == "dlroW ,olleH"
assert s[::2] == "Hlo ol"

s2 = "J" + s[1:]
assert s2 == "Jello, World"

words = "one two three".split()
print(words)
assert words == ["one", "two", "three"]
assert "-".join(words) == "one-two-three"
assert "a,b,,c".split(",") == ["a", "b", "", "c"]  # empty field kept

messy = "   lots of spaces   "
assert messy.strip() == "lots of spaces"
assert messy.lstrip() == "lots of spaces   "
assert "xxhixx".strip("x") == "hi"

assert s.replace("World", "Python") == "Hello, Python"
assert s.find("o") == 4
assert s.find("z") == -1  # -1 instead of raising
assert s.count("l") == 3
assert s.startswith("Hello")
assert s.endswith("World")

assert "123".isdigit()
assert not "12a".isdigit()
assert "abc".isalpha()
assert "World" in s

name = "Sam"
score = 93.4567
msg = f"{name} scored {score:.2f} points"
print(msg)
assert msg == "Sam scored 93.46 points"

assert f"{7:03d}" == "007"
assert f"{'hi':>5}" == "   hi"
assert f"{'hi':<5}|" == "hi   |"
assert f"{1000000:,}" == "1,000,000"
assert f"{0.25:.0%}" == "25%"
x = 10
assert f"{x=}" == "x=10"

old = "%s is %d years old" % ("Bob", 30)
assert old == "Bob is 30 years old"
assert "{} and {}".format("a", "b") == "a and b"

poem = """line one
line two"""
assert poem.count("\n") == 1
assert len(poem.splitlines()) == 2

assert "hello world".title() == "Hello World"
assert "hello world".capitalize() == "Hello world"

word = "racecar"
reversed_word = ""
for ch in word:
    reversed_word = ch + reversed_word
assert reversed_word == word

print("strings ok")
