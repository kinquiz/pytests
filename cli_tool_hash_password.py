#!/usr/bin/env python3
# cli tool hash password
import getpass
import sys

from bcrypt_password_hashing import DEFAULT_ROUNDS, hash_password

MIN_LENGTH = 8


def main(argv: list[str] | None = None, *, rounds: int = DEFAULT_ROUNDS) -> int:
    args = sys.argv[1:] if argv is None else argv

    if len(args) > 1:
        print("usage: cli_tool_hash_password.py [password]", file=sys.stderr)
        return 2

    if args:
        password = args[0]
        print("warning: passing the password as an argument leaves it in shell history", file=sys.stderr)
    else:
        password = getpass.getpass("Password: ")
        if getpass.getpass("Repeat: ") != password:
            print("error: passwords don't match", file=sys.stderr)
            return 1

    if len(password) < MIN_LENGTH:
        print(f"error: password must be at least {MIN_LENGTH} characters", file=sys.stderr)
        return 1

    try:
        hashed = hash_password(password, rounds=rounds)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(hashed)
    # quote it: $ gets interpolated
    print(f"\nDASHBOARD_PASSWORD_HASH='{hashed}'", file=sys.stderr)
    return 0


def _fake_prompts(monkeypatch, *answers: str) -> None:
    replies = iter(answers)
    monkeypatch.setattr(getpass, "getpass", lambda prompt="": next(replies))


def test_prompt_flow_prints_verifiable_hash(monkeypatch, capsys):
    from bcrypt_password_hashing import verify_password

    _fake_prompts(monkeypatch, "longenough", "longenough")
    assert main([], rounds=4) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("$2b$04$")
    assert verify_password("longenough", out)


def test_mismatch(monkeypatch, capsys):
    _fake_prompts(monkeypatch, "longenough", "different1")
    assert main([], rounds=4) == 1
    assert "don't match" in capsys.readouterr().err


def test_too_short(capsys):
    assert main(["short"], rounds=4) == 1
    assert "at least 8" in capsys.readouterr().err


def test_argument_mode_warns(capsys):
    assert main(["longenough"], rounds=4) == 0
    captured = capsys.readouterr()
    assert "shell history" in captured.err
    assert captured.out.startswith("$2b$")


def test_too_many_args(capsys):
    assert main(["a", "b"]) == 2
    assert "usage" in capsys.readouterr().err


if __name__ == "__main__":
    sys.exit(main())
