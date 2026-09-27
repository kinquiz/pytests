# dicts and sets
person = {"name": "Ann", "age": 30, "city": "Berlin"}
print(person)
print(person["name"])
assert person["name"] == "Ann"

person["age"] = 31
person["job"] = "developer"
assert person["age"] == 31
assert len(person) == 4

assert person.get("email") is None
assert person.get("email", "no email") == "no email"

for key in person:
    print(key, "->", person[key])

for key, value in person.items():
    print(key, value)

assert list(person.keys()) == ["name", "age", "city", "job"]  # insertion order (3.7+)

del person["city"]
assert "city" not in person

job = person.pop("job")
assert job == "developer"

text = "the cat and the dog and the bird"
counts = {}
for word in text.split():
    if word in counts:
        counts[word] = counts[word] + 1
    else:
        counts[word] = 1
print(counts)
assert counts["the"] == 3
assert counts["and"] == 2

counts2 = {}
for word in text.split():
    counts2[word] = counts2.get(word, 0) + 1
assert counts == counts2

defaults = {"color": "blue", "size": "M"}
custom = {"size": "L"}
merged = {**defaults, **custom}
assert merged == {"color": "blue", "size": "L"}
merged2 = defaults | custom  # 3.9+
assert merged == merged2

groups = {}
groups.setdefault("a", []).append(1)
groups.setdefault("a", []).append(2)
assert groups == {"a": [1, 2]}

users = {
    "ann": {"age": 30, "langs": ["python", "js"]},
    "bob": {"age": 25, "langs": ["go"]},
}
assert users["ann"]["langs"][0] == "python"

nums = {1, 2, 3, 3, 3}
print(nums)
assert nums == {1, 2, 3}

empty_set = set()  # {} is a dict
assert type({}) == dict
assert type(empty_set) == set

nums.add(4)
nums.discard(100)  # no KeyError, unlike remove()
assert 4 in nums

a = {1, 2, 3, 4}
b = {3, 4, 5}
assert a | b == {1, 2, 3, 4, 5}
assert a & b == {3, 4}
assert a - b == {1, 2}
assert a ^ b == {1, 2, 5}

# set() loses order
dupes = [3, 1, 3, 2, 1]
unique = list(set(dupes))
assert sorted(unique) == [1, 2, 3]

# dict.fromkeys keeps order
unique_ordered = list(dict.fromkeys(dupes))
assert unique_ordered == [3, 1, 2]

print("dicts and sets ok")
