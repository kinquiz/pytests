# file io and json
import json
import os

filename = "practice_notes.txt"

f = open(filename, "w")
f.write("first line\n")
f.write("second line\n")
f.close()

with open(filename, "r") as f:
    content = f.read()
print(content)
assert content == "first line\nsecond line\n"

with open(filename, "a") as f:
    f.write("third line\n")

lines = []
with open(filename) as f:
    for line in f:
        lines.append(line.strip())
assert lines == ["first line", "second line", "third line"]

with open(filename) as f:
    raw_lines = f.readlines()
assert raw_lines[0] == "first line\n"

assert os.path.exists(filename)
os.remove(filename)
assert not os.path.exists(filename)

try:
    with open("this_file_does_not_exist.txt") as f:
        f.read()
except FileNotFoundError:
    print("file not found, as expected")

data = {
    "name": "Ann",
    "age": 30,
    "skills": ["python", "sql"],
    "active": True,
    "manager": None,
}

text = json.dumps(data)
print(text)
assert '"active": true' in text
assert '"manager": null' in text

back = json.loads(text)
assert back == data

print(json.dumps(data, indent=2))

json_file = "practice_data.json"
with open(json_file, "w") as f:
    json.dump(data, f, indent=2)

with open(json_file) as f:
    loaded = json.load(f)
assert loaded["skills"] == ["python", "sql"]
assert loaded == data

# tuples come back as lists
with open(json_file, "w") as f:
    json.dump({"point": (1, 2)}, f)
with open(json_file) as f:
    assert json.load(f) == {"point": [1, 2]}

os.remove(json_file)

try:
    json.loads("{not valid json}")
except json.JSONDecodeError as e:
    print("bad json:", e)

print("file io ok")
