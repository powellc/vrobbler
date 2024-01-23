import pytest
from unittest import mock

from books.koreader import KoReaderImporter, KoReaderBookColumn


@pytest.mark.django_db
@mock.patch("requests.get")
def test_get_or_create_books(get_mock, koreader_book_rows, valid_response):
    get_mock.return_value = valid_response
    importer = KoReaderImporter("test.sqlite3", user_id=1)
    importer.get_or_create_books(koreader_book_rows)
    assert len(importer.BOOK_MAP) == 4


@pytest.mark.django_db
@mock.patch("requests.get")
def test_load_page_data_to_map(get_mock, koreader_rows, valid_response):
    get_mock.return_value = valid_response
    importer = KoReaderImporter("test.sqlite3", user_id=1)
    importer.get_or_create_books(koreader_rows.BOOK_ROWS)

    importer.load_page_data_to_map(koreader_rows.PAGE_STATS_ROWS)
    assert (
        len(importer.BOOK_MAP[1]["pages"])
        == koreader_rows.BOOK_ROWS[0][
            KoReaderBookColumn.TOTAL_READ_PAGES.value
        ]
    )


@pytest.mark.django_db
@mock.patch("requests.get")
def test_build_scrobbles_from_pages(
    get_mock, koreader_rows_for_pages, valid_response
):
    get_mock.return_value = valid_response
    importer = KoReaderImporter("test.sqlite3", user_id=1)
    importer.get_or_create_books(koreader_rows.BOOK_ROWS)
    importer.load_page_data_to_map(koreader_rows.PAGE_STATS_ROWS)
    scrobbles = importer.build_scrobbles_from_pages()
    # Corresponds to number of sessions per book ( 20 pages per session, 120 +/- 15 pages read )
    assert len(scrobbles) == 6
    assert len(scrobbles[0].book_page_data.keys()) == 22
    assert len(scrobbles[1].book_page_data.keys()) == 20
    assert len(scrobbles[2].book_page_data.keys()) == 20
    assert len(scrobbles[3].book_page_data.keys()) == 20
    assert len(scrobbles[4].book_page_data.keys()) == 20
    assert len(scrobbles[5].book_page_data.keys()) == 18
