import datetime


def tz_info(tz_offset: int) -> datetime:
    return datetime.timezone(datetime.timedelta(seconds=tz_offset))


def date(tz_offset: int, minutes_later: int = 10) -> str:
    now: datetime = datetime.datetime.now(tz=tz_info(tz_offset)) + datetime.timedelta(
        minutes=minutes_later
    )
    return f"{now.year}-{now.month}-{now.day}"


def time_minutes_later(tz_offset: int, minutes_later: int) -> str:
    time: datetime = datetime.datetime.now(tz=tz_info(tz_offset)) + datetime.timedelta(
        minutes=minutes_later
    )
    return "{:0>2}:{:0>2}".format(time.hour, time.minute)


def built_post_at(tz_offset: int, date_str: str, time_str: str) -> datetime:
    year, month, day = date_str.split("-")
    hour, minute = time_str.split(":")
    return datetime.datetime(
        year=int(year),
        month=int(month),
        day=int(day),
        hour=int(hour),
        minute=int(minute),
        tzinfo=tz_info(tz_offset),
    )
