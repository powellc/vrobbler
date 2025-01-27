from enum import Enum
from typing import Optional

import pendulum
from meta_yt import YouTube


YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="
IMDB_VIDEO_URL = "https://www.imdb.com/title/tt"


class BookType:
    ...


class BookMetadata:
    title: str
    run_time_seconds: Optional[int]
    authors = Optional[str]
    goodreads_id = Optional[str]
    koreader_data_by_hash = Optional[dict]
    isbn = Optional[str]
    # isbn_13 = Optional[str]
    # isbn_10 = Optional[str]
    pages = Optional[int]
    language = Optional[str]
    first_publish_year = Optional[int]
    summary = Optional[str]

    # General
    cover_url: Optional[str]
    genres: list[str]

    def __init__(self, title: Optional[str] = ""):
        self.title = title

    def as_dict_with_authors_cover_and_genres(self) -> tuple:
        book_dict = vars(self)
        authors = book_dict.pop("authors")
        cover = book_dict.pop("cover_url")
        genres = book_dict.pop("genres")
        return book_dict, authors, cover, genres
