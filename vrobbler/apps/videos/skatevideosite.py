from enum import Enum
from typing import Optional
from bs4 import BeautifulSoup
import requests
import logging


logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0"
)
SKATEVIDEOSITE_URL = "https://www.skatevideosite.com"
SKATEVIDEOSITE_SEARCH_URL = SKATEVIDEOSITE_URL + "/search/?q={title}"


class AmazonAttribute(Enum):
    SERIES = 0
    PAGES = 1
    LANGUAGE = 2
    PUBLISHER = 3
    PUB_DATE = 4
    DIMENSIONS = 5
    ISBN_10 = 6
    ISBN_13 = 7


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


def scrape_data_from_amazon(url) -> dict:
    data_dict = {}
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        import pdb

        pdb.set_trace()
        data_dict["rating"] = get_rating_from_soup(soup)
        data_dict["review"] = get_review_from_soup(soup)
    return data_dict


def lookup_video_from_skatevideosite(title: str) -> Optional[dict]:
    video_metadata = None

    search_url = SKATEVIDEOSITE_SEARCH_URL.format(title=title)
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "accept-language": "en-GB,en;q=0.9",
    }

    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        logger.info(f"Bad http response from SkateVideoSite {response}")
        return video_metadata

    soup = BeautifulSoup(response.text, "html.parser")
    detail_url = ""
    try:
        detail_url = SKATEVIDEOSITE_URL + soup.findAll("a")[12]["href"]
    except IndexError:
        pass

    detail_response = requests.get(detail_url, headers=headers)
    detail_soup = BeautifulSoup(detail_response.text, "html.parser")

    try:
        result = soup.find("div", class_="card-body").find("a")
    except:
        result = None

    if not result:
        logger.info(
            f"No search results found on skatevideosite",
            extra={"title": title},
        )
        return video_metadata

    year = (
        detail_soup.find("span", class_="whitespace-normal")
        .contents[0]
        .replace("(", "")
        .replace(")", "")
    )
    run_time_seconds = (
        int(
            detail_soup.find("div", class_="p-1")
            .contents[-1]
            .contents[0]
            .strip("(")
            .strip("min )")
        )
        * 60
    )

    return {
        "title": str(result.find("img").get("alt").replace(" cover", "")),
        "video_type": "S",
        "year": year,
        "run_time_seconds": run_time_seconds,
        "cover_url": str(result.find("img").get("src")),
    }
