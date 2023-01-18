import datetime

import pytz
from django.conf import settings
from django.utils import timezone


# need to translate to a non-naive timezone, even if timezone == settings.TIME_ZONE, so we can compare two dates
def to_user_timezone(date, profile):
    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE
    return date.replace(tzinfo=pytz.timezone(settings.TIME_ZONE)).astimezone(
        pytz.timezone(timezone)
    )


def to_system_timezone(date, profile):
    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE
    return date.replace(tzinfo=pytz.timezone(timezone)).astimezone(
        pytz.timezone(settings.TIME_ZONE)
    )


def now_user_timezone(profile):
    timezone.activate(pytz.timezone(profile.timezone))
    return timezone.localtime(timezone.now())


def now_system_timezone():
    return (
        datetime.datetime.now()
        .replace(tzinfo=pytz.timezone(settings.TIME_ZONE))
        .astimezone(pytz.timezone(settings.TIME_ZONE))
    )
