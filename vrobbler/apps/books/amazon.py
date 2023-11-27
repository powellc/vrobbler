from enum import Enum
from typing import Optional
from bs4 import BeautifulSoup
import requests
import logging

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0"
)
AMAZON_SEARCH_URL = "https://www.amazon.com/s?k={amazon_id}"


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


def get_amazon_product_dict(amazon_id: str) -> dict:
    data_dict = {}
    url = ""

    search_url = AMAZON_SEARCH_URL.format(amazon_id=amazon_id)
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "accept-language": "en-GB,en;q=0.9",
    }

    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        logger.info(f"Bad http response from Amazon {response}")
        return data_dict

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find("a", class_="a-link-normal")

    if not results:
        logger.info(f"No search results for {amazon_id}")
        return data_dict

    product_url = "https://www.amazon.com" + str(results.get("href", ""))

    data_dict = {}
    response = requests.get(product_url, headers=headers)

    if response.status_code != 200:
        logger.info(f"Bad http response from Amazon {response}")
        return data_dict

    soup = BeautifulSoup(response.text, "html.parser")
    try:
        data_dict["title"] = soup.findAll("span", class_="celwidget")[
            1
        ].text.strip()
        data_dict["cover_url"] = soup.find("img", class_="frontImage").get(
            "src"
        )
        data_dict["summary"] = soup.findAll(
            "div", class_="a-expander-content"
        )[1].text
        meta = soup.findAll("div", class_="rpi-attribute-value")
        data_dict["isbn"] = meta[AmazonAttribute.ISBN_10.value].text.strip()
        pages = meta[AmazonAttribute.PAGES.value].text
        if "pages" in pages:
            data_dict["pages"] = (
                meta[AmazonAttribute.PAGES.value]
                .text.split("pages")[0]
                .strip()
            )
    except IndexError as e:
        logger.error(
            f"Amazon lookup is failing for this product {amazon_id}: {e}"
        )
    except AttributeError as e:
        logger.error(
            f"Amazon lookup is failing for this product {amazon_id}: {e}"
        )

    return data_dict


def lookup_book_from_amazon(amazon_id: str) -> dict:
    top = {}

    return {
        "title": top.get("title"),
        "isbn": isbn,
        "openlibrary_id": ol_id,
        "goodreads_id": get_first("id_goodreads", top),
        "first_publish_year": top.get("first_publish_year"),
        "first_sentence": first_sentence,
        "pages": top.get("number_of_pages_median", None),
        "cover_url": COVER_URL.format(id=ol_id),
        "ol_author_id": ol_author_id,
        "subject_key_list": top.get("subject_key", []),
    }
