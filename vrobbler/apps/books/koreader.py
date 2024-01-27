import codecs
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, List, Optional

import pytz
import requests
from books.models import Author, Book, Page
from books.openlibrary import get_author_openlibrary_id
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import Sum
from pylast import httpx, tempfile
from scrobbles.utils import timestamp_user_tz_to_utc
from stream_sqlite import stream_sqlite

logger = logging.getLogger(__name__)
User = get_user_model()


class KoReaderBookColumn(Enum):
    ID = 0
    TITLE = 1
    AUTHORS = 2
    NOTES = 3
    LAST_OPEN = 4
    HIGHLIGHTS = 5
    PAGES = 6
    SERIES = 7
    LANGUAGE = 8
    MD5 = 9
    TOTAL_READ_TIME = 10
    TOTAL_READ_PAGES = 11


class KoReaderPageStatColumn(Enum):
    ID_BOOK = 0
    PAGE = 1
    START_TIME = 2
    DURATION = 3
    TOTAL_PAGES = 4


def _sqlite_bytes(sqlite_url):
    with httpx.stream("GET", sqlite_url) as r:
        yield from r.iter_bytes(chunk_size=65_536)


# Grace period between page reads for it to be a new scrobble
SESSION_GAP_SECONDS = 1800  #  a half hour


def get_author_str_from_row(row):
    """Given a the raw author string from KoReader, convert it to a single line and
    strip the middle initials, as OpenLibrary lookup usually fails with those.
    """
    ko_authors = row[KoReaderBookColumn.AUTHORS.value].replace("\n", ", ")
    # Strip middle initials, OpenLibrary often fails with these
    return re.sub(" [A-Z]. ", " ", ko_authors)


def lookup_or_create_authors_from_author_str(ko_author_str: str) -> list:
    """Takes a string of authors from KoReader and returns a list
    of Authors from our database
    """
    author_str_list = ko_author_str.split(", ")
    author_list = []
    for author_str in author_str_list:
        logger.debug(f"Looking up author {author_str}")
        # KoReader gave us nothing, bail
        if author_str == "N/A":
            logger.warn(f"KoReader author string is N/A, no authors to find")
            continue

        author = Author.objects.filter(name=author_str).first()
        if not author:
            author = Author.objects.create(
                name=author_str,
                openlibrary_id=get_author_openlibrary_id(author_str),
            )
            author.fix_metadata()
            logger.debug(f"Created author {author}")
        author_list.append(author)
    return author_list


def create_book_from_row(row: list):
    # No KoReader book yet, create it
    author_str = get_author_str_from_row(row)
    total_pages = row[KoReaderBookColumn.PAGES.value]
    run_time = total_pages * Book.AVG_PAGE_READING_SECONDS

    book = Book.objects.create(
        koreader_md5=row[KoReaderBookColumn.MD5.value],
        title=row[KoReaderBookColumn.TITLE.value],
        koreader_id=row[KoReaderBookColumn.ID.value],
        koreader_authors=author_str,
        pages=total_pages,
        run_time_seconds=run_time,
    )
    book.fix_metadata()

    # Add authors
    author_list = lookup_or_create_authors_from_author_str(author_str)
    if author_list:
        book.authors.add(*author_list)

    # self._lookup_authors
    return book


def build_book_map(rows) -> dict:
    """Given an interable of sqlite rows from the books table, lookup existing
    books, create ones that don't exist, and return a mapping of koreader IDs to
    primary key IDs for page creation.

    """
    book_id_map = {}

    for book_row in rows:
        book = Book.objects.filter(
            koreader_md5=book_row[KoReaderBookColumn.MD5.value]
        ).first()

        if not book:
            book = create_book_from_row(book_row)

        book.refresh_from_db()
        total_seconds = 0
        if book_row[KoReaderBookColumn.TOTAL_READ_TIME.value]:
            total_seconds = book_row[KoReaderBookColumn.TOTAL_READ_TIME.value]

        book_id_map[book_row[KoReaderBookColumn.ID.value]] = {
            "book_id": book.id,
            "total_seconds": total_seconds,
        }
    return book_id_map


def build_page_data(page_rows: list, book_map: dict, user_tz=None) -> dict:
    """Given rows of page data from KoReader, parse each row and build
    scrobbles for our user, loading the page data into the page_data
    field on the scrobble instance.
    """
    for page_row in page_rows:
        koreader_book_id = page_row[KoReaderPageStatColumn.ID_BOOK.value]
        if koreader_book_id not in book_map.keys():
            logger.info(
                f"Found pages for book ID {koreader_book_id} not in our history, skipping"
            )
            continue
        if "pages" not in book_map[koreader_book_id].keys():
            book_map[koreader_book_id]["pages"] = {}

        if koreader_book_id not in book_map.keys():
            logger.warn(
                f"Found a page without a corresponding book ID ({koreader_book_id}) in KoReader DB",
                {"page_row": page_row},
            )
            continue

        page_number = page_row[KoReaderPageStatColumn.PAGE.value]
        duration = page_row[KoReaderPageStatColumn.DURATION.value]
        start_ts = page_row[KoReaderPageStatColumn.START_TIME.value]
        # TODO Not sure if this is doing nothing, as timestamps are already assumed in user TZ
        # Maybe we want to save datetime strings with TZ info here?
        # if user_tz:
        #    start_ts = (
        #        datetime.utcfromtimestamp(
        #            int(page_row[KoReaderPageStatColumn.START_TIME.value])
        #        )
        #        .replace(tzinfo=user_tz)
        #        .timestamp()
        #    )
        # else:
        #    logger.warning(
        #        f"Page data built with out user timezone, defaulting to UTC"
        #    )

        book_map[koreader_book_id]["pages"][page_number] = {
            "duration": duration,
            "start_ts": start_ts,
            "end_ts": start_ts + duration,
        }
    return book_map


def build_scrobbles_from_book_map(
    book_map: dict, user: "User"
) -> list["Scrobble"]:
    Scrobble = apps.get_model("scrobbles", "Scrobble")

    scrobbles_to_create = []

    for koreader_book_id, book_dict in book_map.items():
        book_id = book_dict["book_id"]
        if "pages" not in book_dict.keys():
            logger.warn(f"No page data found in book map for {book_id}")
            continue

        should_create_scrobble = False
        scrobble_page_data = {}
        playback_position_seconds = 0
        prev_page_stats = {}

        pages_processed = 0
        total_pages = len(book_map[koreader_book_id]["pages"])

        for page_number, stats in book_map[koreader_book_id]["pages"].items():
            pages_processed += 1
            # Accumulate our page data for this scrobble
            scrobble_page_data[page_number] = stats

            seconds_from_last_page = 0
            if prev_page_stats:
                seconds_from_last_page = stats.get(
                    "end_ts"
                ) - prev_page_stats.get("start_ts")
            playback_position_seconds = playback_position_seconds + stats.get(
                "duration"
            )

            end_of_reading = pages_processed == total_pages
            if seconds_from_last_page > SESSION_GAP_SECONDS or end_of_reading:
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
                        f"Queueing scrobble for {book_id}, page {page_number}"
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
                            book_page_data=scrobble_page_data,
                            book_pages_read=page_number,
                            in_progress=False,
                            played_to_completion=True,
                            long_play_complete=False,
                        )
                    )
                    # Then start over
                    should_create_scrobble = False
                    playback_position_seconds = 0
                    scrobble_page_data = {}

            prev_page_stats = stats
    return scrobbles_to_create


def fix_long_play_stats_for_scrobbles(scrobbles: list) -> None:
    """Given a list of scrobbles, update pages read, long play seconds and check
    for media completion"""

    for scrobble in scrobbles:
        # But if there's a next scrobble, set pages read to their starting page
        #
        if scrobble.previous:
            scrobble.long_play_seconds = scrobble.playback_position_seconds + (
                scrobble.previous.long_play_seconds or 0
            )
            if not scrobble.book_pages_read:
                scrobble.book_pages_read = (
                    scrobble.calc_pages_read()
                    + scrobble.previous.book_pages_read
                )
        else:
            scrobble.long_play_seconds = scrobble.playback_position_seconds
            scrobble.book_pages_read = scrobble.calc_pages_read()

        scrobble.save(update_fields=["book_pages_read", "long_play_seconds"])


def process_koreader_sqlite_file(file_path, user_id) -> list:
    """Given a sqlite file from KoReader, open the book table, iterate
    over rows creating scrobbles from each book found"""
    Scrobble = apps.get_model("scrobbles", "Scrobble")

    new_scrobbles = []
    user = User.objects.filter(id=user_id).first()
    tz = pytz.utc
    if user:
        tz = user.profile.timezone

    is_os_file = "https://" not in file_path
    if is_os_file:
        con = sqlite3.connect(file_path)
        cur = con.cursor()
        book_map = build_book_map(cur.execute("SELECT * FROM book"))
        book_map = build_page_data(
            cur.execute("SELECT * from page_stat_data"), book_map, tz
        )
        new_scrobbles = build_scrobbles_from_book_map(book_map, user)
    else:
        for table_name, pragma_table_info, rows in stream_sqlite(
            _sqlite_bytes(file_path), max_buffer_size=1_048_576
        ):
            logger.debug(f"Found table {table_name} - processing")
            if table_name == "book":
                book_map = build_book_map(rows)

            if table_name == "page_stat_data":
                book_map = build_page_data(rows, book_map, tz)
                new_scrobbles = build_scrobbles_from_book_map(book_map, user)

    logger.info(f"Creating {len(new_scrobbles)} new scrobbles")
    created = []
    if new_scrobbles:
        created = Scrobble.objects.bulk_create(new_scrobbles)
        fix_long_play_stats_for_scrobbles(created)
        logger.info(
            f"Created {len(created)} scrobbles",
            extra={"created_scrobbles": created},
        )
    return created
