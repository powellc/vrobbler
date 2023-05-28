import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from vrobbler.apps.videogames.exceptions import GameNotFound

logger = logging.getLogger(__name__)

MAME_LOOKUP_URL = "http://adb.arcadeitalia.net/dettaglio_mame.php?game_name={query}&search_id=2"


def _strip_and_clean(text):
    return text.replace("\n", " ").rstrip().lstrip()


def _get_title_from_soup(soup) -> Optional[int]:
    title = None
    try:
        title = soup.find("h1", id="page_title").get_text()
    except ValueError:
        pass
    return title


def scrape_game_name_from_adb(name: str) -> str:
    title = ""
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    url = MAME_LOOKUP_URL.format(query=name)
    resp = requests.get(url, headers=headers)
    if not resp.ok:
        raise GameNotFound(f"Lookup failed with code {resp.status_code}")

    soup = BeautifulSoup(resp.text, "html.parser")
    title = _get_title_from_soup(soup).split(" (")[0].split(" / ")[0]

    logger.info(f"Found title {title}")
    if title == "Arcade Database":
        title = ""

    return title
