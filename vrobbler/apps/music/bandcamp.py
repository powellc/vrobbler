import logging
import urllib

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
BANDCAMP_SEARCH_URL = "https://bandcamp.com/search?q={query}&item_type={itype}"


def get_bandcamp_slug(artist_name=None, album_name=None) -> str:
    slug = ""
    if not artist_name:
        return slug

    query = urllib.parse.quote(artist_name)
    item_type = "b"
    class_ = "heading"
    if album_name:
        item_type = "a"
        query = "+".join([query, urllib.parse.quote(album_name)])

    url = BANDCAMP_SEARCH_URL.format(query=query, itype=item_type)
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        logger.info(f"Bad http response from Bandcamp {r}")
        return slug

    soup = BeautifulSoup(r.text, "html")

    results = soup.find("ul", class_="result-items")

    if not results:
        logger.info(f"No search results for {query}")
        return slug

    prime_result = results.findAll("div", class_=class_)

    if not prime_result:
        logger.info(f"Could not find specific result for search {query}")

    result_url = prime_result[0].find_all("a")[0]["href"]
    if item_type == "b":
        slug = result_url.split("/")[2].split(".")[0]
    else:
        slug = result_url.split("?")[0]
    return slug
