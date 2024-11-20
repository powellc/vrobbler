import json
import logging
import urllib
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ALLRECIPE_URL = "https://allrecipe.com/{id}"


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
    except TypeError:
        pass
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
        rating = float(
            soup.find(class_="num").get_text().strip("(").strip(")")
        )
    except AttributeError:
        rating = None
    except ValueError:
        rating = None
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


def get_food_from_allrecipe_id(allrecipe_id: str) -> dict:
    url = ALLRECIPE_URL.format(id=allrecipe_id)
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    response = requests.get(url, headers=headers)

    food_dict = {"allrecipe_id": allrecipe_id}

    if response.status_code != 200:
        logger.warn(
            "Bad response from allrecipe", extra={"response": response}
        )
        return food_dict

    import pdb

    pdb.set_trace()
    soup = BeautifulSoup(response.text, "html.parser")
    food_dict["title"] = get_title_from_soup(soup)
    food_dict["description"] = get_description_from_soup(soup)
    food_dict["allrecipe_rating"] = get_rating_from_soup(soup)

    return food_dict
