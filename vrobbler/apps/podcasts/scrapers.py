import urllib
from typing import Optional
from bs4 import BeautifulSoup
import requests
import logging

logger = logging.getLogger(__name__)

PODCAST_SEARCH_URL = "https://podcasts.google.com/search/{query}"


def _strip_and_clean(text):
    return text.replace("\n", " ").rstrip().lstrip()


def _build_google_url(url):
    return url.replace("./", "https://podcasts.google.com/")

    return


def _get_title_from_soup(soup) -> Optional[int]:
    title = None
    try:
        potential_title = soup.find("div", class_="FyxyKd")
        if potential_title:
            title = _strip_and_clean(potential_title.get_text())
    except ValueError:
        pass
    return title


def _get_url_from_soup(soup) -> Optional[int]:
    url = None
    try:
        url_tag = soup.find("a", class_="yXo2Qc")
        if url_tag:
            url = _build_google_url(url_tag.get("href"))
    except ValueError:
        pass
    return url


def _get_producer_from_soup(soup) -> str:
    pub = ""
    try:
        potential_pub = soup.find("div", class_="J3Ov7d")
        if potential_pub:
            pub = _strip_and_clean(potential_pub.get_text())
    except ValueError:
        pass
    return pub


def _get_description_from_soup(soup) -> str:
    desc = ""
    try:
        potential_desc = soup.find("div", class_="yuTZxb")
        if potential_desc:
            desc = _strip_and_clean(potential_desc.get_text())
    except ValueError:
        pass
    return desc


def _get_img_url_from_soup(soup) -> str:
    url = ""
    try:
        img_tag = soup.find("img", class_="BhVIWc")
        try:
            url = img_tag["src"]
        except IndexError:
            pass
    except ValueError:
        pass
    return url


def scrape_data_from_google_podcasts(title) -> dict:
    data_dict = {}
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    url = PODCAST_SEARCH_URL.format(query=title)
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        data_dict["title"] = _get_title_from_soup(soup)
        data_dict["description"] = _get_description_from_soup(soup)
        data_dict["producer"] = _get_producer_from_soup(soup)
        data_dict["google_url"] = _get_url_from_soup(soup)
        data_dict["image_url"] = _get_img_url_from_soup(soup)
    return data_dict
