import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_ID_URL = (
    "https://boardgamegeek.com/xmlapi/search?search={query}&exact=1"
)
GAME_ID_URL = "https://boardgamegeek.com/xmlapi/boardgame/{id}"


def take_first(thing: Optional[list]) -> str:
    first = ""
    try:
        first = thing[0]
    except IndexError:
        pass

    if first:
        try:
            first = first.get_text()
        except:
            pass

    return first


def lookup_boardgame_id_from_bgg(title: str) -> Optional[int]:
    soup = None
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    game_id = None
    url = SEARCH_ID_URL.format(query=title)
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "xml")

    if soup:
        result = soup.findAll("boardgame")
        if not result:
            return game_id

        game_id = result[0].get("objectid", None)

    return game_id


def lookup_boardgame_from_bgg(lookup_id: str) -> dict:
    soup = None
    game_dict = {}
    headers = {"User-Agent": "Vrobbler 0.11.12"}

    title = ""
    bgg_id = None

    try:
        bgg_id = int(lookup_id)
        logger.debug(f"Using BGG ID {bgg_id} to find board game")
    except ValueError:
        title = lookup_id
        logger.debug(f"Using title {title} to find board game")

    if not bgg_id:
        bgg_id = lookup_boardgame_id_from_bgg(title)

    url = GAME_ID_URL.format(id=bgg_id)
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "xml")

    if soup:
        seconds_to_play = None
        minutes = take_first(soup.findAll("playingtime"))
        if minutes:
            seconds_to_play = int(minutes) * 60

        game_dict = {
            "bggeek_id": bgg_id,
            "title": take_first(soup.findAll("name", primary="true")),
            "description": take_first(soup.findAll("description")),
            "year_published": take_first(soup.findAll("yearpublished")),
            "publisher_name": take_first(soup.findAll("boardgamepublisher")),
            "cover_url": take_first(soup.findAll("image")),
            "min_players": take_first(soup.findAll("minplayers")),
            "max_players": take_first(soup.findAll("maxplayers")),
            "recommended_age": take_first(soup.findAll("age")),
            "run_time_seconds": seconds_to_play,
        }

    return game_dict
