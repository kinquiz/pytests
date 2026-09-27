# pathlib basics
import tempfile
from pathlib import Path

here = Path(__file__).resolve().parent
print("this file lives in", here)
assert (here / "pathlib_basics.py").exists()

p = Path("data") / "users" / "ann.json"
assert p.name == "ann.json"
assert p.stem == "ann"
assert p.suffix == ".json"
assert p.parent == Path("data/users")
assert p.with_suffix(".txt").name == "ann.txt"
assert p.parts == ("data", "users", "ann.json")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    nested = root / "a" / "b"
    nested.mkdir(parents=True, exist_ok=True)
    assert nested.is_dir()

    note = nested / "note.txt"
    note.write_text("hello pathlib\n", encoding="utf-8")
    assert note.read_text(encoding="utf-8") == "hello pathlib\n"
    assert note.stat().st_size == len("hello pathlib\n")

    (root / "one.log").write_text("1")
    (root / "two.log").write_text("2")
    (root / "three.txt").write_text("3")

    logs = sorted(f.name for f in root.glob("*.log"))
    assert logs == ["one.log", "two.log"]

    all_txt = sorted(f.name for f in root.rglob("*.txt"))
    assert all_txt == ["note.txt", "three.txt"]

    children = sorted(c.name for c in root.iterdir())
    assert children == ["a", "one.log", "three.txt", "two.log"]

    moved = (root / "one.log").rename(root / "renamed.log")
    assert moved.exists()
    assert not (root / "one.log").exists()
    moved.unlink()
    assert not moved.exists()
    (root / "gone.txt").unlink(missing_ok=True)

    assert note.relative_to(root) == Path("a/b/note.txt")

    with note.open("a", encoding="utf-8") as f:
        f.write("second line\n")
    assert len(note.read_text().splitlines()) == 2

    blob = root / "data.bin"
    blob.write_bytes(bytes([0, 1, 2, 255]))
    assert blob.read_bytes()[-1] == 255

assert not Path(tmp).exists()

if __name__ == "__main__":
    print("home dir:", Path.home())
    print("pathlib ok")
