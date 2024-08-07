import logging
import pytz
from datetime import datetime, timedelta
from books.models import Book
from django.core.management.base import BaseCommand
from scrobbles.models import Scrobble
from vrobbler.apps.books.koreader import fix_long_play_stats_for_scrobbles
from vrobbler.apps.scrobbles.utils import timestamp_user_tz_to_utc


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        total_books = Book.objects.all().count()
        processed_books = 0

        for book in Book.objects.all():
            for scrobble in book.scrobble_set.all():
                log_data = {
                    "koreader_hash": scrobble.book_koreader_hash,
                    "page_data": scrobble.book_page_data,
                    "pages_read": scrobble.book_pages_read,
                }
                scrobble.log = log_data
                scrobble.save(update_fields=["log"])
            processed_books += 1
            logger.info(f"Processed book {processed_books} of {total_books}")
