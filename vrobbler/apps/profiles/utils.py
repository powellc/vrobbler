import pytz
from django.conf import settings
from django.utils import timezone
import calendar

from datetime import datetime, timedelta

# need to translate to a non-naive timezone, even if timezone == settings.TIME_ZONE, so we can compare two dates
def to_user_timezone(date, profile):
    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE
    return date.astimezone(pytz.timezone(timezone))


def to_system_timezone(date):
    return date.astimezone(pytz.timezone(settings.TIME_ZONE))


def now_user_timezone(profile):
    timezone.activate(pytz.timezone(profile.timezone))
    return timezone.localtime(timezone.now())


def start_of_day(dt, profile) -> datetime:
    """Get the start of the day in the profile's timezone"""
    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE
    tzinfo = pytz.timezone(timezone)
    return datetime.combine(dt, datetime.min.time(), tzinfo)


def end_of_day(dt, profile) -> datetime:
    """Get the start of the day in the profile's timezone"""
    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE
    tzinfo = pytz.timezone(timezone)
    return datetime.combine(dt, datetime.max.time(), tzinfo)


def start_of_week(dt, profile) -> datetime:
    # TODO allow profile to set start of week
    return start_of_day(dt, profile) - timedelta(dt.weekday())


def end_of_week(dt, profile) -> datetime:
    # TODO allow profile to set start of week
    return start_of_week(dt, profile) + timedelta(days=6)


def start_of_month(dt, profile) -> datetime:
    return start_of_day(dt, profile).replace(day=1)


def end_of_month(dt, profile) -> datetime:
    next_month = end_of_day(dt, profile).replace(day=28) + timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - timedelta(days=next_month.day)


def start_of_year(dt, profile) -> datetime:
    return start_of_day(dt, profile).replace(month=1, day=1)
