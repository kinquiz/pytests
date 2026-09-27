# mini todo script
import json
import os

SAVE_FILE = "todos_practice.json"


class Todo:
    def __init__(self, title, priority="normal", done=False):
        self.title = title
        self.priority = priority
        self.done = done

    def __str__(self):
        if self.done:
            mark = "[x]"
        else:
            mark = "[ ]"
        return mark + " " + self.title + " (" + self.priority + ")"

    def to_dict(self):
        return {"title": self.title, "priority": self.priority, "done": self.done}


todos = []


def add_todo(title, priority="normal"):
    if title == "" or title == None:
        raise ValueError("title can't be empty")
    if priority not in ["low", "normal", "high"]:
        raise ValueError("bad priority: " + priority)
    todo = Todo(title, priority)
    todos.append(todo)
    return todo


def complete(title):
    for t in todos:
        if t.title == title:
            t.done = True
            return True
    return False


def pending():
    result = []
    for t in todos:
        if t.done == False:
            result.append(t)
    return result


def count_by_priority():
    counts = {}
    for t in todos:
        if t.priority in counts:
            counts[t.priority] += 1
        else:
            counts[t.priority] = 1
    return counts


def save():
    data = [t.to_dict() for t in todos]
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)


def load():
    loaded = []
    try:
        with open(SAVE_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        return loaded
    for item in data:
        loaded.append(Todo(item["title"], item["priority"], item["done"]))
    return loaded


add_todo("learn python", "high")
add_todo("buy milk")
add_todo("clean room", "low")
add_todo("finish course", "high")

for t in todos:
    print(t)

assert len(todos) == 4
assert complete("buy milk") == True
assert complete("does not exist") == False
assert len(pending()) == 3

counts = count_by_priority()
print(counts)
assert counts == {"high": 2, "normal": 1, "low": 1}

try:
    add_todo("")
except ValueError as e:
    print("error:", e)

try:
    add_todo("something", "urgent")
except ValueError as e:
    print("error:", e)
assert len(todos) == 4

order = {"high": 0, "normal": 1, "low": 2}
sorted_todos = sorted(todos, key=lambda t: order[t.priority])
titles = [t.title for t in sorted_todos]
assert titles[0] in ("learn python", "finish course")
assert titles[-1] == "clean room"

save()
reloaded = load()
assert len(reloaded) == len(todos)
for original, copy in zip(todos, reloaded):
    assert original.title == copy.title
    assert original.done == copy.done
os.remove(SAVE_FILE)

assert load() == []

done_count = len(todos) - len(pending())
summary = f"{done_count}/{len(todos)} done ({done_count / len(todos):.0%})"
print(summary)
assert summary == "1/4 done (25%)"

print("mini script ok")
