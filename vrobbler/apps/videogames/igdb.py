import json
import logging
from datetime import datetime
from typing import Dict, Tuple

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

logger = logging.getLogger(__name__)

User = get_user_model()


def refresh_igdb_api_token(user_id: int) -> Tuple[str, int]:
    user = User.objects.get(id=user_id)
    token_url = REFRESH_TOKEN_URL.format(
        id=user.profile.twitch_client_id,
        secret=user.profile.twitch_client_secret,
    )
    response = requests.post(token_url)
    results = json.loads(response.content)
    return results.get("access_token"), results.get("expires_in")


def lookup_game_from_igdb(client_id: str, token: str, game_id: str) -> Dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Client-ID": client_id,
    }
    fields = "id,name,alternative_names.*,release_dates.*,cover.*,screenshots.*,rating,rating_count"

    game_dict = {}
    if game_id:
        body = f"fields {fields}; where id = {game_id};"
        response = requests.post(GAMES_URL, data=body, headers=headers)
        results = json.loads(response.content)
        if results:
            game = results[0]
            logger.debug(game)

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
                    release_date = datetime.utcfromtimestamp(
                        release_date
                    ).replace(tzinfo=pytz.utc)

            game_dict = {
                "igdb_id": game.get("id"),
                "title": game.get("name"),
                "alternative_name": alt_name,
                "screenshot_url": screenshot_url,
                "cover_url": cover_url,
                "rating": game.get("rating"),
                "rating_count": game.get("rating_count"),
                "release_date": release_date,
            }

    return game_dict
