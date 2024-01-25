import hashlib
import pytest
import random

from vrobbler.apps.books.koreader import KoReaderBookColumn

ordinal = lambda n: "%d%s" % (
    n,
    "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
)
AVERAGE_PAGE_READING_SECONDS = 60


class DummyResponse:
    status_code = 200

    def status_code(self):
        return self.status_code


@pytest.fixture
def valid_response():
    return DummyResponse()


class KoReaderBookRows:
    id = 1
    DEFAULT_STR = "N/A"
    DEFAULT_INT = 0
    DEFAULT_TIME = 1703800469
    BOOK_ROWS = []
    PAGE_STATS_ROWS = []

    def _gen_random_row(self, i):
        wiggle = random.randrange(15)
        title = f"Memoirs, Volume {i}"
        return [
            i,
            title,
            f"Lord Beaverbrook the {ordinal(i)}",
            self.DEFAULT_INT + wiggle / 10,
            self.DEFAULT_TIME + i * wiggle,
            0,
            300 + wiggle,
            self.DEFAULT_STR,
            self.DEFAULT_STR,
            hashlib.md5(title.encode()),
            i * wiggle * 20,
            120,
        ]

    def _generate_random_book_rows(self, book_count):
        if book_count > 0:
            for i in range(1, book_count + 1):
                self.BOOK_ROWS.append(self._gen_random_row(i))

    def _generate_custom_book_row(self, **kwargs):
        title = kwargs.get("title", self.DEFAULT_STR)
        if title and title != "N/A":
            self.BOOK_ROWS.append(
                [
                    kwargs.get("id", self.id),
                    kwargs.get("title", self.DEFAULT_STR),
                    kwargs.get("authors", self.DEFAULT_STR),
                    kwargs.get("notes", self.DEFAULT_INT),
                    kwargs.get("last_open", self.DEFAULT_TIME),
                    kwargs.get("highlights", self.DEFAULT_INT),
                    kwargs.get("pages", self.DEFAULT_INT),
                    kwargs.get("series", self.DEFAULT_STR),
                    kwargs.get("language", self.DEFAULT_STR),
                    hashlib.md5(title.encode()),
                    kwargs.get("total_read_time", self.DEFAULT_INT),
                    kwargs.get("total_read_pages", self.DEFAULT_INT),
                ]
            )

    def _generate_random_page_stats_rows(self):
        for book in self.BOOK_ROWS:
            pages = book[KoReaderBookColumn.PAGES.value]
            pages_per_session = 20

            start_time = book[KoReaderBookColumn.LAST_OPEN.value]
            end_session = False
            for page_num in range(
                1, book[KoReaderBookColumn.TOTAL_READ_PAGES.value] + 1
            ):
                wiggle = random.randrange(5)
                self.PAGE_STATS_ROWS.append(
                    [
                        book[KoReaderBookColumn.ID.value],
                        page_num,
                        start_time,
                        AVERAGE_PAGE_READING_SECONDS + wiggle,
                        pages,
                    ]
                )
                if end_session:
                    start_time += 3600  # one second over an hour, marking a new reading session
                    end_session = False
                else:
                    start_time += AVERAGE_PAGE_READING_SECONDS

                if page_num % pages_per_session == 0:
                    end_session = True

    def __init__(self, book_count=0, **kwargs):
        self._generate_random_book_rows(book_count)
        self._generate_custom_book_row(**kwargs)
        self._generate_random_page_stats_rows()


@pytest.fixture
def koreader_rows():
    return KoReaderBookRows(book_count=1)
