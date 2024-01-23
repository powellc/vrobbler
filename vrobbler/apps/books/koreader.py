import codecs
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, List

import pytz
import requests
from books.models import Author, Book, Page
from books.openlibrary import get_author_openlibrary_id
from django.contrib.auth import get_user_model
from django.db.models import Sum
from pylast import httpx, tempfile
from scrobbles.models import Scrobble
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
SESSION_GAP_SECONDS = 3600  # one hour


class KoReaderImporter:
    # Maps a KoReader book ID to the Book.id and total read time of the book in Django
    # Example:
    # {"KOREADER_DB_ID": {
    #     "book_id": <int>,
    #     "total_seconds": <int>,
    #     "pages": {
    #         <int>: {
    #             "start_ts": <TIMESTAMP>,
    #             "end_ts": <TIMESTAMP>,
    #             "duration": <int>
    #         }
    #     }
    # }
    BOOK_MAP = dict()
    SQLITE_FILE_URL = str
    USER_ID = int

    def __init__(self, sqlite_file_url: str, user_id: int):
        # Map KoReader book IDs to
        self.SQLITE_FILE_URL = sqlite_file_url
        self.USER_ID = user_id
        self.importing_user = User.objects.filter(id=user_id).first()

    def _get_author_str_from_row(self, row):
        """Given a the raw author string from KoReader, convert it to a single line and
        strip the middle initials, as OpenLibrary lookup usually fails with those.
        """
        ko_authors = row[KoReaderBookColumn.AUTHORS.value].replace("\n", ", ")
        # Strip middle initials, OpenLibrary often fails with these
        return re.sub(" [A-Z]. ", " ", ko_authors)

    def _lookup_or_create_authors_from_author_str(
        self, ko_author_str: str
    ) -> list:
        author_str_list = ko_author_str.split(", ")
        author_list = []
        for author_str in author_str_list:
            logger.debug(f"Looking up author {author_str}")
            # KoReader gave us nothing, bail
            if author_str == "N/A":
                logger.warn(
                    f"KoReader author string is N/A, no authors to find"
                )
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

    def get_or_create_books(self, rows):
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
                # No KoReader book yet, create it
                author_str = self._get_author_str_from_row(book_row)
                total_pages = book_row[KoReaderBookColumn.PAGES.value]
                run_time = total_pages * Book.AVG_PAGE_READING_SECONDS

                book = Book.objects.create(
                    koreader_md5=book_row[KoReaderBookColumn.MD5.value],
                    title=book_row[KoReaderBookColumn.TITLE.value],
                    koreader_id=book_row[KoReaderBookColumn.ID.value],
                    koreader_authors=author_str,
                    pages=total_pages,
                    run_time_seconds=run_time,
                )
                book.fix_metadata()

                # Add authors
                author_list = self._lookup_or_create_authors_from_author_str(
                    author_str
                )
                if author_list:
                    book.authors.add(*author_list)

                # self._lookup_authors

            book.refresh_from_db()
            total_seconds = 0
            if book_row[KoReaderBookColumn.TOTAL_READ_TIME.value]:
                total_seconds = book_row[
                    KoReaderBookColumn.TOTAL_READ_TIME.value
                ]

            book_id_map[book_row[KoReaderBookColumn.ID.value]] = {
                "book_id": book.id,
                "total_seconds": total_seconds,
            }
        self.BOOK_MAP = book_id_map

    def load_page_data_to_map(self, rows: Iterable) -> List[Scrobble]:
        """Given rows of page data from KoReader, parse each row and build
        scrobbles for our user, loading the page data into the page_data
        field on the scrobble instance.
        """
        for page_row in rows:
            koreader_book_id = page_row[KoReaderPageStatColumn.ID_BOOK.value]
            if "pages" not in self.BOOK_MAP[koreader_book_id].keys():
                self.BOOK_MAP[koreader_book_id]["pages"] = {}

            if koreader_book_id not in self.BOOK_MAP.keys():
                logger.warn(
                    f"Found a page without a corresponding book ID ({koreader_book_id}) in KoReader DB",
                    {"page_row": page_row},
                )
                continue

            page_number = page_row[KoReaderPageStatColumn.PAGE.value]
            duration = page_row[KoReaderPageStatColumn.DURATION.value]
            start_ts = page_row[KoReaderPageStatColumn.START_TIME.value]
            if self.importing_user:
                start_ts = timestamp_user_tz_to_utc(
                    page_row[KoReaderPageStatColumn.START_TIME.value],
                    self.importing_user.timezone,
                )

            self.BOOK_MAP[koreader_book_id]["pages"][page_number] = {
                "duration": duration,
                "start_ts": start_ts,
                "end_ts": start_ts + duration,
            }

    def build_scrobbles_from_pages(self) -> List[Scrobble]:
        scrobbles_to_create = []

        for koreader_book_id, book_dict in self.BOOK_MAP.items():
            book_id = book_dict["book_id"]
            if "pages" not in book_dict.keys():
                logger.warn(f"No page data found in book map for {book_id}")
                continue

            should_create_scrobble = False
            scrobble_page_data = {}
            playback_position_seconds = 0
            prev_page_stats = {}

            pages_processed = 0
            total_pages = len(self.BOOK_MAP[koreader_book_id]["pages"])

            for page_number, stats in self.BOOK_MAP[koreader_book_id][
                "pages"
            ].items():
                pages_processed += 1
                # Accumulate our page data for this scrobble
                scrobble_page_data[page_number] = stats

                seconds_from_last_page = 0
                if prev_page_stats:
                    seconds_from_last_page = stats.get(
                        "end_ts"
                    ) - prev_page_stats.get("start_ts")
                playback_position_seconds = (
                    playback_position_seconds + stats.get("duration")
                )

                if (
                    seconds_from_last_page > SESSION_GAP_SECONDS
                    or pages_processed == total_pages
                ):
                    should_create_scrobble = True

                print(
                    f"Seconds: {seconds_from_last_page} - {should_create_scrobble}"
                )
                if should_create_scrobble:
                    first_page_in_scrobble = list(scrobble_page_data.keys())[0]
                    timestamp = datetime.utcfromtimestamp(
                        int(
                            scrobble_page_data.get(first_page_in_scrobble).get(
                                "start_ts"
                            )
                        )
                    ).replace(tzinfo=pytz.utc)

                    scrobble = Scrobble.objects.filter(
                        timestamp=timestamp,
                        book_id=book_id,
                        # user_id=self.importing_user.id,
                    ).first()
                    if not scrobble:
                        logger.info(
                            f"Queueing scrobble for {book_id}, page {page_number}"
                        )
                        scrobbles_to_create.append(
                            Scrobble(
                                book_id=book_id,
                                # user_id=self.importing_user.id,
                                source="KOReader",
                                media_type=Scrobble.MediaType.BOOK,
                                timestamp=timestamp,
                                played_to_completion=True,
                                playback_position_seconds=playback_position_seconds,
                                in_progress=False,
                                book_page_data=scrobble_page_data,
                                book_pages_read=page_number,
                                long_play_complete=False,
                            )
                        )
                        # Then start over
                        should_create_scrobble = False
                        playback_position_seconds = 0
                        scrobble_page_data = {}

                prev_page_stats = stats
        return scrobbles_to_create

    def _enrich_koreader_scrobbles(self, scrobbles: list) -> None:
        """Given a list of scrobbles, update pages read, long play seconds and check
        for media completion"""

        for scrobble in scrobbles:
            # But if there's a next scrobble, set pages read to their starting page
            #
            if scrobble.next:
                scrobble.book_pages_read = scrobble.next.book_pages_read - 1
            scrobble.long_play_seconds = scrobble.book.page_set.filter(
                number__lte=scrobble.book_pages_read
            ).aggregate(Sum("duration_seconds"))["duration_seconds__sum"]

            scrobble.save(
                update_fields=["book_pages_read", "long_play_seconds"]
            )

    def process_file(self):
        new_scrobbles = []

        for table_name, pragma_table_info, rows in stream_sqlite(
            _sqlite_bytes(self.FILE_URL), max_buffer_size=1_048_576
        ):
            logger.debug(f"Found table {table_name} - processing")
            if table_name == "book":
                self.get_or_create_books(rows)

            if table_name == "page_stat_data":
                self.build_scrobbles_from_page_data(rows)

                # new_scrobbles = build_scrobbles_from_pages(
                #    rows, book_id_map, user_id
                # )
                # logger.debug(f"Creating {len(new_scrobbles)} new scrobbles")

        created = []
        if new_scrobbles:
            created = Scrobble.objects.bulk_create(new_scrobbles)
            self._enrich_koreader_scrobbles(created)
            logger.info(
                f"Created {len(created)} scrobbles",
                extra={"created_scrobbles": created},
            )
        return created

    def process_koreader_sqlite_file(self, file_path, user_id) -> list:
        """Given a sqlite file from KoReader, open the book table, iterate
        over rows creating scrobbles from each book found"""
        # Create a SQL connection to our SQLite database
        con = sqlite3.connect(file_path)
        cur = con.cursor()

        book_id_map = self.get_or_create_books(
            cur.execute("SELECT * FROM book")
        )
        new_scrobbles = self.build_scrobbles_from_pages(
            cur.execute("SELECT * from page_stat_data"), book_id_map, user_id
        )

        created = []
        if new_scrobbles:
            created = Scrobble.objects.bulk_create(new_scrobbles)
            self._enrich_koreader_scrobbles(created)
            logger.info(
                f"Created {len(created)} scrobbles",
                extra={"created_scrobbles": created},
            )
        return created

    def process_koreader_sqlite(file_path: str, user_id: int) -> list:
        is_os_file = "https://" not in file_path

        if is_os_file:
            created = process_koreader_sqlite_file(file_path, user_id)
        else:
            created = process_koreader_sqlite_url(file_path, user_id)
        return created
