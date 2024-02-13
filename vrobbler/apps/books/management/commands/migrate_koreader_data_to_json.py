import logging
import pytz
from datetime import datetime
from books.models import Book
from django.core.management.base import BaseCommand
from scrobbles.models import Scrobble
from vrobbler.apps.books.koreader import fix_long_play_stats_for_scrobbles
from vrobbler.apps.scrobbles.utils import timestamp_user_tz_to_utc


logger = logging.getLogger(__name__)

# Grace period between page reads for it to be a new scrobble
SESSION_GAP_SECONDS = 1800  #  a half hour


class Command(BaseCommand):
    def handle(self, *args, **options):
        scrobbles_to_create = []

        for book in Book.objects.filter(koreader_id__isnull=False):
            for scrobble in book.scrobble_set.all():
                scrobble.scrobbledpage_set.all().delete()
            book.scrobble_set.all().delete()

            koreader_data = book.koreader_data_by_hash or {}
            if book.koreader_md5:
                koreader_data[book.koreader_md5] = {
                    "title": book.title,
                    "book_id": book.koreader_id,
                    "author_str": book.koreader_authors,
                    "pages": book.pages,
                }
            book.koreader_data_by_hash = koreader_data
            book.save(update_fields=["koreader_data_by_hash"])

            # Next parse all this book's pages into new scrobbles
            should_create_scrobble = False
            scrobble_page_data = {}
            playback_position_seconds = 0
            prev_page = None

            pages_processed = 0
            total_pages = book.pages
            for page in book.page_set.order_by("number"):
                user = page.user
                book_id = page.book.id
                pages_processed += 1
                scrobble_page_data[page.number] = {
                    "duration": page.duration_seconds,
                    "start_ts": page.start_time.timestamp(),
                    "end_ts": page.end_time.timestamp(),
                }
                seconds_from_last_page = 0
                if prev_page:
                    seconds_from_last_page = (
                        page.end_time.timestamp()
                        - prev_page.start_time.timestamp()
                    )
                playback_position_seconds = (
                    playback_position_seconds + page.duration_seconds
                )

                end_of_reading = pages_processed == total_pages
                big_jump_to_this_page = False
                if prev_page:
                    big_jump_to_this_page = (
                        page.number - prev_page.number
                    ) > 10
                if (
                    seconds_from_last_page > SESSION_GAP_SECONDS
                    and not big_jump_to_this_page
                ):
                    should_create_scrobble = True

                if should_create_scrobble:
                    first_page = scrobble_page_data.get(
                        list(scrobble_page_data.keys())[0]
                    )
                    last_page = scrobble_page_data.get(
                        list(scrobble_page_data.keys())[-1]
                    )
                    start_ts = int(first_page.get("start_ts"))
                    end_ts = start_ts + playback_position_seconds

                    timestamp = datetime.fromtimestamp(start_ts).replace(
                        tzinfo=user.profile.tzinfo
                    )
                    stop_timestamp = datetime.fromtimestamp(end_ts).replace(
                        tzinfo=user.profile.tzinfo
                    )
                    # Add a shim here temporarily to fix imports while we were in France
                    # if date is between 10/15 and 12/15, cast it to Europe/Central
                    if (
                        datetime(2023, 10, 15).replace(
                            tzinfo=pytz.timezone("Europe/Paris")
                        )
                        <= timestamp
                        <= datetime(2023, 12, 15).replace(
                            tzinfo=pytz.timezone("Europe/Paris")
                        )
                    ):
                        timestamp.replace(tzinfo=pytz.timezone("Europe/Paris"))

                    scrobble = Scrobble.objects.filter(
                        timestamp=timestamp,
                        book_id=book_id,
                        user_id=user.id,
                    ).first()
                    if scrobble:
                        logger.info(
                            f"Found existing scrobble {scrobble}, updating"
                        )
                        scrobble.book_page_data = scrobble_page_data
                        scrobble.playback_position_seconds = (
                            scrobble.calc_reading_duration()
                        )
                        scrobble.save(
                            update_fields=[
                                "book_page_data",
                                "playback_position_seconds",
                            ]
                        )
                    if not scrobble:
                        logger.info(
                            f"Queueing scrobble for {book_id}, page {page.number}"
                        )
                        scrobbles_to_create.append(
                            Scrobble(
                                book_id=book_id,
                                user_id=user.id,
                                source="KOReader",
                                media_type=Scrobble.MediaType.BOOK,
                                timestamp=timestamp,
                                stop_timestamp=stop_timestamp,
                                playback_position_seconds=playback_position_seconds,
                                book_koreader_hash=list(
                                    book.koreader_data_by_hash.keys()
                                )[0],
                                book_page_data=scrobble_page_data,
                                book_pages_read=page.number,
                                in_progress=False,
                                played_to_completion=True,
                                long_play_complete=False,
                            )
                        )
                        # Then start over
                        should_create_scrobble = False
                        playback_position_seconds = 0
                        scrobble_page_data = {}

                prev_page = page

        created = Scrobble.objects.bulk_create(scrobbles_to_create)
        for scrobble in created:
            fix_long_play_stats_for_scrobbles(scrobble)
