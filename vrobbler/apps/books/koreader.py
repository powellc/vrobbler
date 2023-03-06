import logging
from datetime import datetime
import sqlite3
from enum import Enum

import pytz

from books.models import Author, Book, Page
from scrobbles.models import Scrobble

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


def process_pages_for_book(book_id, sqlite_file_path):
    con = sqlite3.connect(sqlite_file_path)
    cur = con.cursor()

    book = Book.objects.filter(koreader_id=book_id).first()
    if not book:
        logger.error(f"No book found with KoReader ID of {book_id}")
        return

    page_table = cur.execute(
        f"SELECT * FROM page_stat_data where id_book={book_id}"
    )
    new_pages = []
    for page_row in page_table:
        page_number = page_row[KoReaderPageStatColumn.PAGE.value]
        page, page_created = Page.objects.get_or_create(
            book=book, number=page_number
        )
        if page_created:
            ts = page_row[KoReaderPageStatColumn.START_TIME.value]
            page.start_time = datetime.utcfromtimestamp(ts).replace(
                tzinfo=pytz.utc
            )
            page.duration_seconds = page_row[
                KoReaderPageStatColumn.DURATION.value
            ]
            page.save()
            new_pages.append(page)
    logger.info("Added {len(new_pages)} for book {book}")
    return new_pages


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
        authors = book_row[KoReaderBookColumn.AUTHORS.value].split("\n")
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
            title=book_row[KoReaderBookColumn.TITLE.value]
        )

        if created:
            pages = book_row[KoReaderBookColumn.PAGES.value]
            run_time = pages * book.AVG_PAGE_READING_SECONDS
            run_time_ticks = run_time * 1000
            book_dict = {
                "title": book_row[KoReaderBookColumn.TITLE.value],
                "pages": book_row[KoReaderBookColumn.PAGES.value],
                "koreader_md5": book_row[KoReaderBookColumn.MD5.value],
                "koreader_id": int(book_row[KoReaderBookColumn.ID.value]),
                "koreader_authors": book_row[KoReaderBookColumn.AUTHORS.value],
                "run_time": run_time,
                "run_time_ticks": run_time_ticks,
            }
            Book.objects.filter(pk=book.id).update(**book_dict)
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
        process_pages_for_book(book.koreader_id, sqlite_file_path)

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
        if book.progress_for_user(user_id) >= Book.COMPLETION_PERCENT:
            new_scrobble.long_play_complete = True

        logger.debug(f"Queued scrobble {new_scrobble} for creation")
        new_scrobbles.append(new_scrobble)

    # Be sure to close the connection
    con.close()

    created = Scrobble.objects.bulk_create(new_scrobbles)
    logger.info(
        f"Created {len(created)} scrobbles",
        extra={"created_scrobbles": created},
    )
    return created
