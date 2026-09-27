# logging instead of print
import io
import logging

log = logging.getLogger(__name__)


def divide(a: float, b: float) -> float | None:
    log.debug("divide called with a=%s b=%s", a, b)  # lazy %-formatting
    if b == 0:
        log.warning("tried to divide %s by zero", a)
        return None
    return a / b


def risky() -> None:
    try:
        {}["missing"]
    except KeyError:
        log.exception("lookup failed")


def capture_logs(level: int) -> str:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    root = logging.getLogger()
    old_level = root.level
    root.addHandler(handler)
    root.setLevel(level)
    try:
        divide(1, 2)
        divide(1, 0)
        risky()
    finally:
        root.removeHandler(handler)
        root.setLevel(old_level)
    return stream.getvalue()


if __name__ == "__main__":
    # entry point only, never in library code
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    log.info("starting up")
    log.debug("you won't see this at INFO level")

    # logger name is __main__ when run directly
    debug_output = capture_logs(logging.DEBUG)
    assert "DEBUG:__main__:divide called with a=1 b=2" in debug_output
    assert "WARNING:__main__:tried to divide 1 by zero" in debug_output
    assert "ERROR:__main__:lookup failed" in debug_output
    assert "Traceback" in debug_output

    warning_output = capture_logs(logging.WARNING)
    assert "DEBUG" not in warning_output
    assert "WARNING" in warning_output

    parent = logging.getLogger("myapp")
    child = logging.getLogger("myapp.db")
    assert child.parent is parent
    parent.setLevel(logging.ERROR)
    assert child.getEffectiveLevel() == logging.ERROR

    logging.getLogger("some.noisy.library").setLevel(logging.WARNING)

    log.info("logging ok")
