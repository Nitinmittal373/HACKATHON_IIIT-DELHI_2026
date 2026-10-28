"""Days and months in Indian time, which is when the people using the site count their day."""

from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def day_start(now: datetime) -> datetime:
    return now.astimezone(IST).replace(hour=0, minute=0, second=0, microsecond=0)


def next_day(now: datetime) -> datetime:
    return day_start(now) + timedelta(days=1)


def month_start(now: datetime) -> datetime:
    return day_start(now).replace(day=1)


def next_month(now: datetime) -> datetime:
    return (month_start(now) + timedelta(days=32)).replace(day=1)
