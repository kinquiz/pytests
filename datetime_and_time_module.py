# datetime and time module
import time
from datetime import date, datetime, timedelta, timezone

# fixed dates keep asserts deterministic
d = date(2024, 2, 28)
assert d + timedelta(days=1) == date(2024, 2, 29)
assert d + timedelta(days=2) == date(2024, 3, 1)
assert d.weekday() == 2  # monday == 0
assert d.isoformat() == "2024-02-28"

start = date(2024, 1, 1)
end = date(2024, 12, 25)
assert (end - start).days == 359

dt = datetime(2024, 3, 15, 14, 30, 0)
print(dt)
assert dt.strftime("%Y-%m-%d %H:%M") == "2024-03-15 14:30"
assert dt.strftime("%d/%m/%y") == "15/03/24"
assert dt.strftime("%A") == "Friday"

parsed = datetime.strptime("2024-03-15 14:30", "%Y-%m-%d %H:%M")
assert parsed == dt

assert datetime.fromisoformat("2024-03-15T14:30:00") == dt

# store aware UTC datetimes
naive_now = datetime.now()
aware_now = datetime.now(timezone.utc)
assert naive_now.tzinfo is None
assert aware_now.tzinfo is timezone.utc
try:
    naive_now < aware_now
except TypeError:
    print("can't compare naive and aware datetimes")

utc_dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
ts = utc_dt.timestamp()
assert ts == 1704067200.0
assert datetime.fromtimestamp(ts, tz=timezone.utc) == utc_dt

plus_two = timezone(timedelta(hours=2))
local = utc_dt.astimezone(plus_two)
assert local.hour == 2
assert local == utc_dt  # same instant

td = timedelta(days=1, hours=2, minutes=30)
assert td.total_seconds() == 95400
assert td * 2 == timedelta(days=2, hours=5)

cutoff = datetime(2024, 3, 1, tzinfo=timezone.utc) - timedelta(days=30)
created = datetime(2024, 1, 15, tzinfo=timezone.utc)
assert created < cutoff

t0 = time.time()  # wall clock, can jump
m0 = time.monotonic()  # never goes backwards, use for durations
time.sleep(0.05)
elapsed = time.monotonic() - m0
assert elapsed >= 0.05
assert time.time() >= t0

p0 = time.perf_counter()  # highest resolution
sum(range(1000))
assert time.perf_counter() - p0 >= 0

st = time.gmtime(0)
assert st.tm_year == 1970

if __name__ == "__main__":
    print("now (utc):", aware_now.isoformat(timespec="seconds"))
    print("datetime ok")
