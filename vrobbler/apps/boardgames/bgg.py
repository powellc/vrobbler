from typing import Optional

import requests
from bs4 import BeautifulSoup

SEARCH_ID_URL = "https://boardgamegeek.com/xmlapi/search?search={query}"
GAME_ID_URL = "https://boardgamegeek.com/xmlapi/boardgame/{id}"


def take_first(thing: Optional[list]) -> str:
    first = ""
    try:
        first = thing[0]
    except IndexError:
        pass

    if first:
        first = first.get_text()

    return first


def get_id_from_bgg(title):
    soup = ""
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    url = SEARCH_ID_URL.format(query=title)
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "xml")
    return soup


def get_game_by_id_from_bgg(game_id):
    soup = None
    game_dict = {}
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    url = GAME_ID_URL.format(id=game_id)
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "xml")

    if soup:
        seconds_to_play = None
        minutes = take_first(soup.findAll("playingtime"))
        if minutes:
            seconds_to_play = int(minutes) * 60

        game_dict = {
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
