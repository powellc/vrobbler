import pytest
from unittest import mock

from books.koreader import (
    KoReaderBookColumn,
    build_book_map,
    build_page_data,
    build_scrobbles_from_book_map,
)


@pytest.mark.django_db
@mock.patch("requests.get")
def test_build_book_map(get_mock, koreader_rows, valid_response):
    get_mock.return_value = valid_response
    book_map = build_book_map(koreader_rows.BOOK_ROWS)
    assert len(book_map) == 1


@pytest.mark.django_db
@mock.patch("requests.get")
def test_load_page_data_to_map(get_mock, koreader_rows, valid_response):
    get_mock.return_value = valid_response
    book_map = build_book_map(koreader_rows.BOOK_ROWS)

    book_map = build_page_data(koreader_rows.PAGE_STATS_ROWS, book_map)
    assert (
        len(book_map[1]["pages"])
        == koreader_rows.BOOK_ROWS[0][
            KoReaderBookColumn.TOTAL_READ_PAGES.value
        ]
    )


@pytest.mark.django_db
@mock.patch("requests.get")
def test_build_scrobbles_from_pages(
    get_mock, koreader_rows, demo_user, valid_response
):
    get_mock.return_value = valid_response
    book_map = build_book_map(koreader_rows.BOOK_ROWS)
    book_map = build_page_data(koreader_rows.PAGE_STATS_ROWS, book_map)

    scrobbles = build_scrobbles_from_book_map(book_map, demo_user)
    # Corresponds to number of sessions per book ( 20 pages per session, 120 +/- 15 pages read )
    expected_scrobbles = 6 * len(book_map.keys())
    assert len(scrobbles) == expected_scrobbles
    assert len(scrobbles[0].book_page_data.keys()) == 22
    assert len(scrobbles[1].book_page_data.keys()) == 20
    assert len(scrobbles[2].book_page_data.keys()) == 20
    assert len(scrobbles[3].book_page_data.keys()) == 20
    assert len(scrobbles[4].book_page_data.keys()) == 20
    assert len(scrobbles[5].book_page_data.keys()) == 18
