import urllib
from typing import Optional
from bs4 import BeautifulSoup
import requests
import logging

logger = logging.getLogger(__name__)

ALLMUSIC_SEARCH_URL = "https://www.allmusic.com/search/{subpath}/{query}"


def strip_and_clean(text):
    return text.strip("\n").rstrip().lstrip()


def get_rating_from_soup(soup) -> Optional[int]:
    rating = None
    try:
        potential_rating = soup.find("div", class_="allmusic-rating")
        if potential_rating:
            rating = int(strip_and_clean(potential_rating.get_text()))
    except ValueError:
        pass
    return rating


def get_review_from_soup(soup) -> str:
    review = ""
    try:
        potential_text = soup.find("div", class_="text")
        if potential_text:
            review = strip_and_clean(potential_text.get_text())
    except ValueError:
        pass
    return review


def scrape_data_from_allmusic(url) -> dict:
    data_dict = {}
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        data_dict["rating"] = get_rating_from_soup(soup)
        data_dict["review"] = get_review_from_soup(soup)
    return data_dict


def get_allmusic_slug(artist_name=None, album_name=None) -> str:
    slug = ""
    if not artist_name:
        return slug

    subpath = "artists"
    class_ = "name"
    query = urllib.parse.quote(artist_name)
    if album_name:
        subpath = "albums"
        class_ = "title"
        query = "+".join([query, urllib.parse.quote(album_name)])

    url = ALLMUSIC_SEARCH_URL.format(subpath=subpath, query=query)
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        logger.info(f"Bad http response from Allmusic {r}")
        return slug

    soup = BeautifulSoup(r.text, "html.parser")
    results = soup.find("ul", class_="search-results")

    if not results:
        logger.info(f"No search results for {query}")
        return slug

    prime_result = results.findAll("div", class_=class_)

    if not prime_result:
        logger.info(f"Could not find specific result for search {query}")

    result_url = prime_result[0].find_all("a")[0]["href"]
    slug = result_url.split("/")[-1:][0]

    return slug
