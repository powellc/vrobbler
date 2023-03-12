import json
import logging
import urllib

import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://openlibrary.org/search.json?title={title}"
ISBN_URL = "https://openlibrary.org/isbn/{isbn}.json"
SEARCH_URL = "https://openlibrary.org/search.json?title={title}"
COVER_URL = "https://covers.openlibrary.org/b/olid/{id}-L.jpg"
AUTHOR_URL = "https://openlibrary.org/authors/{id}.json"
AUTHOR_IMAGE_URL = "https://covers.openlibrary.org/a/olid/{id}-L.jpg"


def get_first(key: str, result: dict) -> str:
    obj = ""
    if obj_list := result.get(key):
        obj = obj_list[0]
    return obj


def lookup_author_from_openlibrary(olid: str) -> dict:
    author_url = AUTHOR_URL.format(id=olid)
    response = requests.get(author_url)

    if response.status_code != 200:
        logger.warn(f"Bad response from OL: {response.status_code}")
        return {}

    results = json.loads(response.content)

    if not results:
        logger.warn(f"No author results found from OL for {olid}")
        return {}

    remote_ids = results.get("remote_ids", {})
    bio = ""
    if results.get("bio"):
        try:
            bio = results.get("bio").get("value")
        except AttributeError:
            bio = results.get("bio")
    return {
        "name": results.get("name"),
        "openlibrary_id": olid,
        "wikipedia_url": results.get("wikipedia"),
        "wikidata_id": remote_ids.get("wikidata"),
        "isni": remote_ids.get("isni"),
        "goodreads_id": remote_ids.get("goodreads"),
        "librarything_id": remote_ids.get("librarything"),
        "amazon_id": remote_ids.get("amazon"),
        "bio": bio,
        "author_headshot_url": AUTHOR_IMAGE_URL.format(id=olid),
    }


def lookup_book_from_openlibrary(title: str, author: str = None) -> dict:
    title_quoted = urllib.parse.quote(title)
    search_url = SEARCH_URL.format(title=title_quoted)
    response = requests.get(search_url)

    if response.status_code != 200:
        logger.warn(f"Bad response from OL: {response.status_code}")
        return {}

    results = json.loads(response.content)

    if len(results.get("docs")) == 0:
        logger.warn(f"No results found from OL for {title}")
        return {}

    top = results.get("docs")[0]
    ol_id = top.get("cover_edition_key")
    ol_author_id = get_first("author_key", top)
    first_sentence = ""
    if top.get("first_sentence"):
        try:
            first_sentence = top.get("first_sentence")[0].get("value")
        except AttributeError:
            first_sentence = top.get("first_sentence")[0]
    return {
        "title": top.get("title"),
        "isbn": top.get("isbn")[0],
        "openlibrary_id": ol_id,
        "goodreads_id": get_first("id_goodreads", top),
        "first_publish_year": top.get("first_publish_year"),
        "first_sentence": first_sentence,
        "pages": top.get("number_of_pages_median", None),
        "cover_url": COVER_URL.format(id=ol_id),
        "ol_author_id": ol_author_id,
    }
