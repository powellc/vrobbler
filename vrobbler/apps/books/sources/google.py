import json
import logging

import pendulum
import requests
from books.metadata import BookMetadata
from django.conf import settings

API_KEY = settings.GOOGLE_API_KEY
GOOGLE_BOOKS_URL = (
    "https://www.googleapis.com/books/v1/volumes?q={title}&key={key}"
)

logger = logging.getLogger(__name__)


def lookup_book_from_google(title: str) -> BookMetadata:
    book_metadata = BookMetadata(title=title)

    url = GOOGLE_BOOKS_URL.format(title=title, key=API_KEY)
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.warning(
            "Bad response from Google", extra={"response": response}
        )
        return book_metadata

    google_result = (
        json.loads(response.content).get("items", [{}])[0].get("volumeInfo")
    )
    publish_date = pendulum.parse(google_result.get("publishedDate"))

    isbn_13 = ""
    isbn_10 = ""
    for ident in google_result.get("industryIdentifiers", []):
        if ident.get("type") == "ISBN_13":
            isbn_13 = ident.get("identifier")
        if ident.get("type") == "ISBN_10":
            isbn_10 = ident.get("identifier")
    book_metadata.title = google_result.get("title")
    if google_result.get("subtitle"):
        book_metadata.title = ": ".join(
            [google_result.get("title"), google_result.get("subtitle")]
        )
    book_metadata.authors = google_result.get("authors")
    book_metadata.publisher = google_result.get("publisher")
    book_metadata.first_publish_year = publish_date.year
    book_metadata.pages = google_result.get("pageCount")
    book_metadata.isbn_13 = isbn_13
    book_metadata.isbn_10 = isbn_10
    book_metadata.publish_date = google_result.get("publishedDate")
    book_metadata.language = google_result.get("language")
    book_metadata.summary = google_result.get("description")
    book_metadata.genres = google_result.get("categories")
    book_metadata.cover_url = (
        google_result.get("imageLinks", {})
        .get("thumbnail")
        .replace("zoom=1", "zoom=15")
        .replace("&edge=curl", "")
    )

    book_metadata.run_time_seconds = book_metadata.pages * getattr(
        settings, "AVERAGE_PAGE_READING_SECONDS", 60
    )

    return book_metadata
