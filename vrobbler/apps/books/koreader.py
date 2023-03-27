import codecs
import logging
import os
import sqlite3
from datetime import datetime
from enum import Enum
from typing import Iterable, List

import pytz
import requests
from books.models import Author, Book, Page
from pylast import httpx, tempfile
from scrobbles.models import Scrobble
from stream_sqlite import stream_sqlite
from vrobbler.apps.books.openlibrary import get_author_openlibrary_id

logger = logging.getLogger(__name__)


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


def get_book_map_from_sqlite(rows: Iterable) -> dict:
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
            book, created = Book.objects.get_or_create(
                title=book_row[KoReaderBookColumn.TITLE.value]
            )

            if created:
                total_pages = book_row[KoReaderBookColumn.PAGES.value]
                run_time = total_pages * book.AVG_PAGE_READING_SECONDS
                ko_authors = book_row[
                    KoReaderBookColumn.AUTHORS.value
                ].replace("\n", ", ")
                book_dict = {
                    "title": book_row[KoReaderBookColumn.TITLE.value],
                    "pages": total_pages,
                    "koreader_md5": book_row[KoReaderBookColumn.MD5.value],
                    "koreader_id": int(book_row[KoReaderBookColumn.ID.value]),
                    "koreader_authors": ko_authors,
                    "run_time_seconds": run_time,
                }
                Book.objects.filter(pk=book.id).update(**book_dict)

                # Add authors
                authors = book_row[KoReaderBookColumn.AUTHORS.value].split(
                    "\n"
                )
                author_list = []
                for author_str in authors:
                    logger.debug(f"Looking up author {author_str}")
                    if author_str == "N/A":
                        continue

                    author, created = Author.objects.get_or_create(
                        name=author_str
                    )
                    if created:
                        author.openlibrary_id = get_author_openlibrary_id(
                            author_str
                        )
                        author.save(update_fields=["openlibrary_id"])
                        author.fix_metadata()
                        logger.debug(f"Created author {author}")
                    book.authors.add(author)

                # This will try to fix metadata by looking it up on OL
                book.fix_metadata()

        playback_position_seconds = 0
        if book_row[KoReaderBookColumn.TOTAL_READ_TIME.value]:
            playback_position_seconds = book_row[
                KoReaderBookColumn.TOTAL_READ_TIME.value
            ]

        pages_read = 0
        if book_row[KoReaderBookColumn.TOTAL_READ_PAGES.value]:
            pages_read = int(
                book_row[KoReaderBookColumn.TOTAL_READ_PAGES.value]
            )
        timestamp = datetime.utcfromtimestamp(
            book_row[KoReaderBookColumn.LAST_OPEN.value]
        ).replace(tzinfo=pytz.utc)
        book.refresh_from_db()
        book_id_map[book.koreader_id] = book.id

    return book_id_map


def build_scrobbles_from_pages(
    rows: Iterable, book_id_map: dict, user_id: int
) -> List[Scrobble]:
    new_scrobbles = []

    new_scrobbles = []
    for page_row in rows:
        koreader_id = page_row[KoReaderPageStatColumn.ID_BOOK.value]
        page_number = page_row[KoReaderPageStatColumn.PAGE.value]
        ts = page_row[KoReaderPageStatColumn.START_TIME.value]
        book_id = book_id_map[koreader_id]

        page, page_created = Page.objects.get_or_create(
            book_id=book_id, number=page_number, user_id=user_id
        )
        if page_created:
            page.start_time = datetime.utcfromtimestamp(ts).replace(
                tzinfo=pytz.utc
            )
            page.duration_seconds = page_row[
                KoReaderPageStatColumn.DURATION.value
            ]
            page.save(update_fields=["start_time", "duration_seconds"])
            page.refresh_from_db()

        if page.is_scrobblable:
            # Page number is a placeholder, we'll re-preocess this after creation
            logger.debug(
                f"Queueing scrobble for {page.book}, page {page.number}"
            )
            new_scrobble = Scrobble(
                book_id=page.book_id,
                user_id=user_id,
                source="KOReader",
                timestamp=page.start_time,
                played_to_completion=True,
                in_progress=False,
                book_pages_read=page_number,
                long_play_complete=False,
            )
            new_scrobbles.append(new_scrobble)
    return new_scrobbles


def enrich_koreader_scrobbles(scrobbles: list) -> None:
    """Given a list of scrobbles, update pages read, long play seconds and check
    for media completion"""

    for scrobble in scrobbles:
        if scrobble.next:
            # Set pages read to the starting page of the next scrobble minus one, if it exists
            scrobble.book_pages_read = scrobble.next.book_pages_read - 1
            scrobble.save(update_fields=["book_pages_read"])
        else:
            # Set pages read to the last page we have
            scrobble.book_pages_read = scrobble.book.page_set.last().number

        scrobble.save(update_fields=["book_pages_read", "long_play_complete"])


def process_koreader_sqlite_url(file_url, user_id) -> list:
    book_id_map = {}
    new_scrobbles = []

    for table_name, pragma_table_info, rows in stream_sqlite(
        _sqlite_bytes(file_url), max_buffer_size=1_048_576
    ):
        if table_name == "book":
            book_id_map = get_book_map_from_sqlite(rows)

        if table_name == "page":
            new_scrobbles = build_scrobbles_from_pages(
                rows, book_id_map, user_id
            )

    created = []
    if new_scrobbles:
        created = Scrobble.objects.bulk_create(new_scrobbles)
        enrich_koreader_scrobbles(created)
        logger.info(
            f"Created {len(created)} scrobbles",
            extra={"created_scrobbles": created},
        )
    return created


def process_koreader_sqlite_file(file_path, user_id) -> list:
    """Given a sqlite file from KoReader, open the book table, iterate
    over rows creating scrobbles from each book found"""
    # Create a SQL connection to our SQLite database
    con = sqlite3.connect(file_path)
    cur = con.cursor()

    book_id_map = get_book_map_from_sqlite(cur.execute("SELECT * FROM book"))
    new_scrobbles = build_scrobbles_from_pages(
        cur.execute("SELECT * from page_stat_data"), book_id_map, user_id
    )

    created = []
    if new_scrobbles:
        created = Scrobble.objects.bulk_create(new_scrobbles)
        enrich_koreader_scrobbles(created)
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
