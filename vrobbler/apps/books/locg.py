#!/usr/bin/env python3

from enum import Enum
from typing import Optional
from bs4 import BeautifulSoup
import requests
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "accept-language": "en-GB,en;q=0.9",
}
LOCG_WRTIER_URL = ""
LOCG_WRITER_DETAIL_URL = "https://leagueofcomicgeeks.com/people/{slug}"
LOCG_SEARCH_URL = (
    "https://leagueofcomicgeeks.com/search/ajax_issues?query={query}"
)
LOCG_DETAIL_URL = "https://leagueofcomicgeeks.com/comic/{locg_slug}"


def strip_and_clean(text):
    return text.strip("\n").strip()


def get_rating_from_soup(soup) -> Optional[int]:
    rating = None
    try:
        potential_rating = soup.find("div", class_="allmusic-rating")
        if potential_rating:
            rating = int(strip_and_clean(potential_rating.get_text()))
    except ValueError:
        pass
    return rating


def lookup_comic_writer_by_locg_slug(slug: str) -> dict:
    data_dict = {}
    writer_url = LOCG_WRITER_DETAIL_URL.format(slug=slug)

    response = requests.get(writer_url, headers=HEADERS)

    if response.status_code != 200:
        logger.info(f"Bad http response from LOCG {response}")
        return data_dict

    soup = BeautifulSoup(response.text, "html.parser")
    data_dict["locg_slug"] = slug
    data_dict["name"] = soup.find("h1").text.strip()
    data_dict["photo_url"] = soup.find("div", class_="avatar").img.get("src")

    return data_dict


def lookup_comic_by_locg_slug(slug: str) -> dict:
    data_dict = {}
    product_url = LOCG_DETAIL_URL.format(locg_slug=slug)

    response = requests.get(product_url, headers=HEADERS)

    if response.status_code != 200:
        logger.info(f"Bad http response from LOCG {response}")
        return data_dict

    soup = BeautifulSoup(response.text, "html.parser")
    try:
        data_dict["title"] = soup.find("h1").text.strip()
        data_dict["summary"] = soup.find("p").text.strip()
        data_dict["cover_url"] = (
            soup.find("div", class_="cover-art").find("img").get("src")
        )
        attrs = soup.findAll("div", class_="details-addtl-block")
        try:
            data_dict["pages"] = (
                attrs[1]
                .find("div", class_="value")
                .text.split("pages")[0]
                .strip()
            )
        except IndexError:
            logger.warn(f"No ISBN field")
        try:
            data_dict["isbn"] = (
                attrs[3].find("div", class_="value").text.strip()
            )
        except IndexError:
            logger.warn(f"No ISBN field")

        writer_slug = None
        try:
            writer_slug = (
                soup.findAll("div", class_="name")[5]
                .a.get("href")
                .split("people/")[1]
            )
        except IndexError:
            logger.warn(f"No wrtier found")
        if writer_slug:
            data_dict["locg_writer_slug"] = writer_slug

    except AttributeError:
        logger.warn(f"Trouble parsing HTML, elements missing")

    return data_dict


def lookup_comic_from_locg(title: str) -> dict:
    search_url = LOCG_SEARCH_URL.format(query=title)
    response = requests.get(search_url, headers=HEADERS)

    if response.status_code != 200:
        logger.warn(f"Bad http response from LOCG {response}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        slug = soup.findAll("a")[1].get("href").split("comic/")[1]
    except IndexError:
        logger.warn(f"No comic found on LOCG for {title}")
        return {}

    return lookup_comic_by_locg_slug(slug)
