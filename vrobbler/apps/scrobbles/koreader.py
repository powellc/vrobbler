import logging
from datetime import datetime
import sqlite3
from enum import Enum

import pytz

from books.models import Author, Book
from scrobbles.models import Scrobble
from django.utils import timezone

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


def process_koreader_sqlite_file(sqlite_file_path, user_id):
    """Given a sqlite file from KoReader, open the book table, iterate
    over rows creating scrobbles from each book found"""
    # Create a SQL connection to our SQLite database
    con = sqlite3.connect(sqlite_file_path)
    cur = con.cursor()

    # Return all results of query
    book_table = cur.execute("SELECT * FROM book")
    new_scrobbles = []
    for book_row in book_table:
        authors = book_row[KoReaderBookColumn.AUTHORS.value].split('\n')
        author_list = []
        for author_str in authors:
            logger.debug(f"Looking up author {author_str}")

            if author_str == "N/A":
                continue

            author, created = Author.objects.get_or_create(name=author_str)
            if created:
                author.fix_metadata()
            author_list.append(author)
            logger.debug(f"Found author {author}, created: {created}")

        book, created = Book.objects.get_or_create(
            koreader_md5=book_row[KoReaderBookColumn.MD5.value]
        )

        if created:
            book.title = book_row[KoReaderBookColumn.TITLE.value]
            book.pages = book_row[KoReaderBookColumn.PAGES.value]
            book.koreader_id = int(book_row[KoReaderBookColumn.ID.value])
            book.koreader_authors = book_row[KoReaderBookColumn.AUTHORS.value]
            book.run_time_ticks = int(book_row[KoReaderBookColumn.PAGES.value])
            book.save(
                update_fields=[
                    "title",
                    "pages",
                    "koreader_id",
                    "koreader_authors",
                ]
            )
            book.fix_metadata()
            if author_list:
                book.authors.add(*[a.id for a in author_list])

        playback_position = int(
            book_row[KoReaderBookColumn.TOTAL_READ_TIME.value]
        )
        playback_position_ticks = playback_position * 1000
        pages_read = int(book_row[KoReaderBookColumn.TOTAL_READ_PAGES.value])
        timestamp = datetime.utcfromtimestamp(
            book_row[KoReaderBookColumn.LAST_OPEN.value]
        ).replace(tzinfo=pytz.utc)

        new_scrobble = Scrobble(
            book_id=book.id,
            user_id=user_id,
            source="KOReader",
            timestamp=timestamp,
            playback_position_ticks=playback_position_ticks,
            playback_position=playback_position,
            played_to_completion=True,
            in_progress=False,
            book_pages_read=pages_read,
        )

        existing = Scrobble.objects.filter(
            timestamp=timestamp, book=book
        ).first()
        if existing:
            logger.debug(f"Skipping existing scrobble {new_scrobble}")
            continue

        logger.debug(f"Queued scrobble {new_scrobble} for creation")
        new_scrobbles.append(new_scrobble)

    # Be sure to close the connection
    con.close()

    created = Scrobble.objects.bulk_create(new_scrobbles)
    logger.info(
        f"Created {len(created)} scrobbles",
        extra={'created_scrobbles': created},
    )
    return created
