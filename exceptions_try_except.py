# exceptions try except
try:
    result = 10 / 0
except ZeroDivisionError:
    result = None
    print("can't divide by zero")
assert result is None

try:
    int("abc")
except ValueError as e:
    print("error was:", e)
    error_message = str(e)
assert "invalid literal" in error_message

def safe_get(items, index):
    try:
        return items[index]
    except IndexError:
        return "index too big"
    except TypeError:
        return "index must be a number"

assert safe_get([1, 2, 3], 1) == 2
assert safe_get([1, 2, 3], 10) == "index too big"
assert safe_get([1, 2, 3], "a") == "index must be a number"

def to_number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

assert to_number("3.5") == 3.5
assert to_number("nope") == 0.0
assert to_number(None) == 0.0

log = []
try:
    x = int("5")
except ValueError:
    log.append("error")
else:
    log.append("no error")  # only if no exception
finally:
    log.append("finally")
assert log == ["no error", "finally"]

log = []
try:
    x = int("five")
except ValueError:
    log.append("error")
else:
    log.append("no error")
finally:
    log.append("finally")
assert log == ["error", "finally"]

def set_age(age):
    if age < 0:
        raise ValueError("age can't be negative")
    return age

try:
    set_age(-1)
    raised = False
except ValueError:
    raised = True
assert raised

d = {"a": 1}
try:
    d["b"]
except KeyError as e:
    print("missing key:", e)

def check_raises(func, *args):
    try:
        func(*args)
    except Exception:
        return True
    return False

assert check_raises(int, "x") == True
assert check_raises(int, "7") == False

try:
    [].pop()
except Exception as e:
    print(type(e).__name__, "-", e)
    caught_type = type(e)
assert caught_type == IndexError

def parse_or_explain(text):
    try:
        return int(text)
    except ValueError:
        print("couldn't parse", text)
        raise

try:
    parse_or_explain("oops")
except ValueError:
    print("re-raised ok")

print("exceptions ok")
