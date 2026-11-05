from datetime import datetime, timedelta, timezone


MSK = timezone(timedelta(hours=3))


def now_iso():
    return datetime.now(MSK).replace(microsecond=0).isoformat()


def lease_window(ttl_minutes):
    acquired = datetime.now(MSK).replace(microsecond=0)
    expires = acquired + timedelta(minutes=ttl_minutes)
    return acquired, expires
