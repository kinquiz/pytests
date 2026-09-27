# bcrypt password hashing
import functools
import time

import bcrypt

DEFAULT_ROUNDS = 12  # ~250ms/hash; tests use 4
BCRYPT_MAX_BYTES = 72  # bcrypt>=5 rejects longer input


def hash_password(password: str, *, rounds: int = DEFAULT_ROUNDS) -> str:
    raw = password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_BYTES:
        raise ValueError(f"password is longer than {BCRYPT_MAX_BYTES} bytes")
    # salt is embedded in the hash
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=rounds)).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:
        # malformed hash or >72 bytes
        return False


@functools.cache
def _dummy_hash(rounds: int = DEFAULT_ROUNDS) -> str:
    return hash_password("dummy-password-that-never-matches", rounds=rounds)


def authenticate(username: str, password: str, users: dict[str, str], *, rounds: int = DEFAULT_ROUNDS) -> bool:
    stored = users.get(username)
    if stored is None:
        # equal timing so usernames can't be probed
        verify_password(password, _dummy_hash(rounds))
        return False
    return verify_password(password, stored)


def test_hash_and_verify():
    hashed = hash_password("hunter2", rounds=4)
    assert hashed.startswith("$2b$04$")
    assert verify_password("hunter2", hashed)
    assert not verify_password("hunter3", hashed)


def test_same_password_different_hashes():
    assert hash_password("same", rounds=4) != hash_password("same", rounds=4)


def test_verify_handles_garbage_hash():
    assert not verify_password("x", "not-a-bcrypt-hash")


def test_rejects_overlong_password():
    import pytest

    with pytest.raises(ValueError, match="72 bytes"):
        hash_password("a" * 73, rounds=4)


def test_authenticate():
    users = {"admin": hash_password("correct horse", rounds=4)}
    assert authenticate("admin", "correct horse", users, rounds=4)
    assert not authenticate("admin", "wrong", users, rounds=4)
    assert not authenticate("nobody", "correct horse", users, rounds=4)


def test_unknown_user_still_pays_bcrypt_cost():
    rounds = 10
    users = {"admin": hash_password("pw", rounds=rounds)}
    _dummy_hash(rounds)  # warm cache

    def timed(username: str) -> float:
        start = time.perf_counter()
        authenticate(username, "wrong", users, rounds=rounds)
        return time.perf_counter() - start

    known, unknown = timed("admin"), timed("ghost")
    # without the dummy hash, ghost would be ~0ms
    assert unknown > known * 0.5
