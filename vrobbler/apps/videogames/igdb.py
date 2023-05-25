import json
import logging
from datetime import datetime
from typing import Dict, Tuple

from django.conf import settings
import pytz
import requests
from django.contrib.auth import get_user_model

TWITCH_AUTH_BASE = "https://id.twitch.tv/"
REFRESH_TOKEN_URL = (
    TWITCH_AUTH_BASE
    + "oauth2/token?client_id={id}&client_secret={secret}&grant_type=client_credentials"
)
SEARCH_URL = "https://api.igdb.com/v4/search"
GAMES_URL = "https://api.igdb.com/v4/games"
ALT_NAMES_URL = "https://api.igdb.com/v4/alternative_names"
SCREENSHOT_URL = "https://api.igdb.com/v4/screenshots"
COVER_URL = "https://api.igdb.com/v4/covers"

IGDB_CLIENT_ID = getattr(settings, "IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = getattr(settings, "IGDB_CLIENT_SECRET")

logger = logging.getLogger(__name__)

User = get_user_model()


def get_igdb_token() -> str:
    token_url = REFRESH_TOKEN_URL.format(
        id=IGDB_CLIENT_ID, secret=IGDB_CLIENT_SECRET
    )
    response = requests.post(token_url)
    results = json.loads(response.content)
    return results.get("access_token")


def lookup_game_id_from_gdb(name: str) -> str:

    headers = {
        "Authorization": f"Bearer {get_igdb_token()}",
        "Client-ID": IGDB_CLIENT_ID,
    }
    if "(" in name:
        name = name.split(" (")[0]

    body = f'fields name,game,published_at; search "{name}"; limit 20;'
    response = requests.post(SEARCH_URL, data=body, headers=headers)
    results = json.loads(response.content)
    if not results:
        logger.warn(f"Search of game on IGDB failed for name {name}")
        return ""

    return results[0]["game"]


def lookup_game_from_igdb(name_or_igdb_id: str) -> Dict:
    """Given credsa and an IGDB game ID, lookup the game metadata and return it
    in a dictionary mapped to our internal game fields

    """
    try:
        igdb_id = int(name_or_igdb_id)
    except ValueError:
        igdb_id = lookup_game_id_from_gdb(name_or_igdb_id)

    headers = {
        "Authorization": f"Bearer {get_igdb_token()}",
        "Client-ID": IGDB_CLIENT_ID,
    }
    fields = "id,name,alternative_names.*,genres.*,release_dates.*,cover.*,screenshots.*,rating,rating_count,summary"

    game_dict = {}
    body = f"fields {fields}; where id = {igdb_id};"
    response = requests.post(GAMES_URL, data=body, headers=headers)
    results = json.loads(response.content)
    if not results:
        logger.warn(f"Lookup of game on IGDB failed for ID {igdb_id}")
        return game_dict

    game = results[0]

    alt_name = None
    if "alternative_names" in game.keys():
        alt_name = game.get("alternative_names")[0].get("name")
    screenshot_url = None
    if "screenshots" in game.keys():
        screenshot_url = "https:" + game.get("screenshots")[0].get(
            "url"
        ).replace("t_thumb", "t_screenshot_big_2x")
    cover_url = None
    if "cover" in game.keys():
        cover_url = "https:" + game.get("cover").get("url").replace(
            "t_thumb", "t_cover_big_2x"
        )
    release_date = None
    if "release_dates" in game.keys():
        release_date = game.get("release_dates")[0].get("date")
        if release_date:
            release_date = datetime.utcfromtimestamp(release_date).replace(
                tzinfo=pytz.utc
            )
    genres = []
    if "genres" in game.keys():
        for genre in game.get("genres"):
            genres.append(genre["name"])

    game_dict = {
        "igdb_id": game.get("id"),
        "title": game.get("name"),
        "alternative_name": alt_name,
        "screenshot_url": screenshot_url,
        "cover_url": cover_url,
        "rating": game.get("rating"),
        "rating_count": game.get("rating_count"),
        "release_date": release_date,
        "summary": game.get("summary"),
        "genres": genres,
    }

    return game_dict
