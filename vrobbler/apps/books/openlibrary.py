import json
import requests
import logging

logger = logging.getLogger(__name__)

SEARCH_URL = "https://openlibrary.org/search.json?title={title}"
ISBN_URL = "https://openlibrary.org/isbn/{isbn}.json"
SEARCH_URL = "https://openlibrary.org/search.json?title={title}"
COVER_URL = "https://covers.openlibrary.org/b/olid/{id}-L.jpg"


def get_first(key: str, result: dict) -> str:
    obj = ""
    if obj_list := result.get(key):
        obj = obj_list[0]
    return obj


def lookup_book_from_openlibrary(title: str, author: str = None) -> dict:
    search_url = SEARCH_URL.format(title=title)
    response = requests.get(search_url)

    if response.status_code != 200:
        logger.warn(f"Bad response from OL: {response.status_code}")
        return {}

    results = json.loads(response.content)

    if len(results.get("docs")) == 0:
        logger.warn(f"No results found from OL for {title}")
        return {}

    top = results.get("docs")[0]
    if author and author not in top["author_name"]:
        logger.warn(
            f"Lookup for {title} found top result with mismatched author"
        )
    ol_id = top.get("cover_edition_key")
    return {
        "title": top.get("title"),
        "isbn": top.get("isbn")[0],
        "openlibrary_id": top.get("cover_edition_key"),
        "author_name": get_first("author_name", top),
        "author_openlibrary_id": get_first("author_key", top),
        "goodreads_id": get_first("id_goodreads", top),
        "first_publish_year": top.get("first_publish_year"),
        "pages": top.get("number_of_pages_median"),
        "cover_url": COVER_URL.format(id=ol_id),
    }
