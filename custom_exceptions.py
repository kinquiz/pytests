# custom exceptions


class BotError(Exception):
    # catch-all base for bot errors
    pass


class PermissionDenied(BotError):
    def __init__(self, command_name: str, required: str | None = None) -> None:
        self.command_name = command_name
        self.required = required
        message = f"you don't have permission to use '{command_name}'"
        if required:
            message += f" (requires {required})"
        super().__init__(message)


class NotFound(BotError):
    def __init__(self, kind: str, identifier: object) -> None:
        self.kind = kind
        self.identifier = identifier
        super().__init__(f"{kind} {identifier!r} not found")


class RateLimited(BotError):
    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after
        super().__init__(f"slow down, try again in {retry_after:.0f}s")


ADMINS = {1}
USERS = {1: "ann", 2: "bob"}


def run_command(user_id: int, name: str) -> str:
    if user_id not in USERS:
        raise NotFound("user", user_id)
    if name.startswith("admin_") and user_id not in ADMINS:
        raise PermissionDenied(name, required="admin")
    return f"{USERS[user_id]} ran {name}"


def handle(user_id: int, name: str) -> str:
    try:
        return run_command(user_id, name)
    except PermissionDenied as e:
        return f"denied: {e.command_name}"
    except BotError as e:
        return f"error: {e}"


if __name__ == "__main__":
    assert handle(1, "admin_ban") == "ann ran admin_ban"
    assert handle(2, "ping") == "bob ran ping"
    assert handle(2, "admin_ban") == "denied: admin_ban"
    assert handle(99, "ping") == "error: user 99 not found"

    try:
        run_command(2, "admin_purge")
    except PermissionDenied as e:
        assert e.command_name == "admin_purge"
        assert e.required == "admin"
        assert str(e) == "you don't have permission to use 'admin_purge' (requires admin)"
        assert isinstance(e, BotError)
        assert isinstance(e, Exception)

    try:
        try:
            int("abc")
        except ValueError as original:
            raise NotFound("config value", "abc") from original
    except NotFound as e:
        assert isinstance(e.__cause__, ValueError)
        print("chained:", repr(e.__cause__))

    err = RateLimited(4.6)
    assert str(err) == "slow down, try again in 5s"

    print("custom exceptions ok")
