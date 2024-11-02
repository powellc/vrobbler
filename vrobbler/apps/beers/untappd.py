import json
import logging
import urllib
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

UNTAPPD_URL = "https://untappd.com/beer/{id}"


def get_first(key: str, result: dict) -> str:
    obj = ""
    if obj_list := result.get(key):
        obj = obj_list[0]
    return obj


def get_title_from_soup(soup) -> str:
    title = ""
    try:
        title = soup.find("h1").get_text()
    except AttributeError:
        pass
    except ValueError:
        pass
    return title


def get_description_from_soup(soup) -> str:
    desc = ""
    try:
        desc = (
            soup.find(class_="beer-descrption-read-less")
            .get_text()
            .replace("Show Less", "")
            .strip()
        )
    except AttributeError:
        pass
    except ValueError:
        pass
    return desc


def get_styles_from_soup(soup) -> list[str]:
    styles = []
    try:
        styles = soup.find("p", class_="style").get_text().split(" - ")
    except AttributeError:
        pass
    except ValueError:
        pass
    return styles


def get_abv_from_soup(soup) -> Optional[float]:
    abv = None
    try:
        abv = soup.find(class_="abv").get_text()
        if abv:
            abv = float(abv.strip("\n").strip("% ABV").strip())
    except AttributeError:
        pass
    except ValueError:
        pass
    if "N/A" in abv:
        abv = None
    return abv


def get_ibu_from_soup(soup) -> Optional[int]:
    ibu = None
    try:
        ibu = soup.find(class_="ibu").get_text()
        if ibu:
            ibu = int(ibu.strip("\n").strip(" IBU").strip())
    except AttributeError:
        pass
    except ValueError:
        ibu = None
    return ibu


def get_rating_from_soup(soup) -> str:
    rating = ""
    try:
        rating = soup.find(class_="num").get_text().strip("(").strip(")")
    except AttributeError:
        pass
    except ValueError:
        pass
    return rating


def get_producer_id_from_soup(soup) -> str:
    id = ""
    try:
        id = soup.find(class_="brewery").find("a")["href"].strip("/")
    except ValueError:
        pass
    except IndexError:
        pass
    return id


def get_producer_name_from_soup(soup) -> str:
    name = ""
    try:
        name = soup.find(class_="brewery").find("a").get_text()
    except AttributeError:
        pass
    except ValueError:
        pass
    return name


def get_beer_from_untappd_id(untappd_id: str) -> dict:
    beer_url = UNTAPPD_URL.format(id=untappd_id)
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    response = requests.get(beer_url, headers=headers)
    beer_dict = {"untappd_id": untappd_id}

    if response.status_code != 200:
        logger.warn(
            "Bad response from untappd.com", extra={"response": response}
        )
        return beer_dict

    soup = BeautifulSoup(response.text, "html.parser")
    beer_dict["untappd_id"] = untappd_id
    beer_dict["title"] = get_title_from_soup(soup)
    beer_dict["description"] = get_description_from_soup(soup)
    beer_dict["styles"] = get_styles_from_soup(soup)
    beer_dict["abv"] = get_abv_from_soup(soup)
    beer_dict["ibu"] = get_ibu_from_soup(soup)
    beer_dict["untappd_rating"] = get_rating_from_soup(soup)
    beer_dict["producer__untappd_id"] = get_producer_id_from_soup(soup)
    beer_dict["producer__name"] = get_producer_name_from_soup(soup)

    return beer_dict
