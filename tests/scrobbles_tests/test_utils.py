from datetime import datetime
import pytz
from django.contrib.auth import get_user_model

from vrobbler.apps.scrobbles.utils import timestamp_user_tz_to_utc


def test_timestamp_user_tz_to_utc():
    timestamp = timestamp_user_tz_to_utc(
        1685561082, pytz.timezone("US/Eastern")
    )
    assert timestamp == datetime(2023, 5, 31, 23, 24, 42, tzinfo=pytz.utc)
