#!/usr/bin/env python3
import logging
import pytz
from datetime import datetime, timedelta
from books.models import Book
from django.core.management.base import BaseCommand
from scrobbles.models import Scrobble
from vrobbler.apps.books.koreader import fix_long_play_stats_for_scrobbles
from vrobbler.apps.scrobbles.utils import timestamp_user_tz_to_utc


logger = logging.getLogger(__name__)

# Grace period between page reads for it to be a new scrobble
SESSION_GAP_SECONDS = 1800  #  a half hour

def update_scrobble_from_page_data(scrobble, commit=True):
    page_list = list(scrobble.book_page_data.items())
    first_page_start_ts = datetime.fromtimestamp(page_list[0][1]["start_ts"])
    last_page_end_ts = datetime.fromtimestamp(page_list[-1][1]["end_ts"])

    if (
        datetime(2023, 10, 15) <= first_page_start_ts <= datetime(2023, 12, 15)
    ):
        first_page_start_ts.replace(tzinfo=pytz.timezone("Europe/Paris"))
        last_page_end_ts.replace(tzinfo=pytz.timezone("Europe/Paris"))
    else:
        first_page_start_ts.replace(tzinfo=pytz.timezone("US/Eastern"))
        last_page_end_ts.replace(tzinfo=pytz.timezone("US/Eastern"))

    scrobble.timestamp = first_page_start_ts
    scrobble.stop_timestamp = last_page_end_ts
    if commit:
        scrobble.save(update_fields=["timestamp", "stop_timestamp"])


class Command(BaseCommand):
    def handle(self, *args, **options):
        scrobbles_to_create = []

        for scrobble in Scrobble.objects.filter(media_type="Book", source="KOReader"):
            update_scrobble_from_page_data(scrobble)
