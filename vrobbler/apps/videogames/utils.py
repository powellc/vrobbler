import logging
from typing import Optional

import requests
from django.core.files.base import ContentFile
from videogames.models import VideoGame, VideoGamePlatform

from videogames.howlongtobeat import lookup_game_from_hltb
from videogames.igdb import lookup_game_from_igdb

logger = logging.getLogger(__name__)


def get_or_create_videogame(
    name_or_id: str, force_update=False
) -> Optional[VideoGame]:
    """Look up game by name or ID from HowLongToBeat"""

    game_dict = lookup_game_from_hltb(name_or_id)

    if not game_dict:
        return

    platform_ids = []
    for platform in game_dict.get("platforms"):
        p, _created = VideoGamePlatform.objects.get_or_create(name=platform)
        platform_ids.append(p.id)
    game_dict.pop("platforms")

    game, game_created = VideoGame.objects.get_or_create(
        hltb_id=game_dict.get("hltb_id")
    )

    if game_created or force_update:
        cover_url = game_dict.pop("cover_url")

        VideoGame.objects.filter(pk=game.id).update(**game_dict)
        game.refresh_from_db()

        # Associate plaforms
        if platform_ids:
            game.platforms.add(*platform_ids)

        # Go get cover image if the URL is present
        if cover_url and not game.hltb_cover:
            headers = {"User-Agent": "Vrobbler 0.11.12"}
            r = requests.get(cover_url, headers=headers)
            logger.debug(r.status_code)
            if r.status_code == 200:
                fname = f"{game.title}_cover_{game.uuid}.jpg"
                game.hltb_cover.save(fname, ContentFile(r.content), save=True)
                logger.debug("Loaded cover image from HLtB")

    return game


def load_game_data_from_igdb(game_id: int) -> Optional[VideoGame]:
    """Look up game, if it doesn't exist, lookup data from igdb"""
    game = VideoGame.objects.filter(id=game_id).first()
    if not game:
        logger.warn(f"Video game with ID {game_id} not found")
        return

    if not game.igdb_id:
        logger.warn(f"Video game has no IGDB ID")
        return

    logger.info(f"Looking up video game {game.igdb_id}")
    game_dict = lookup_game_from_igdb(game.igdb_id)
    if not game_dict:
        logger.warn(f"No game data found on IGDB for ID {game.igdb_id}")
        return

    screenshot_url = game_dict.pop("screenshot_url")
    cover_url = game_dict.pop("cover_url")

    VideoGame.objects.filter(pk=game.id).update(**game_dict)
    game.refresh_from_db()

    if not game.screenshot:
        r = requests.get(screenshot_url)
        if r.status_code == 200:
            fname = f"{game.title}_{game.uuid}.jpg"
            game.screenshot.save(fname, ContentFile(r.content), save=True)

    if not game.cover:
        r = requests.get(cover_url)
        if r.status_code == 200:
            fname = f"{game.title}_{game.uuid}.jpg"
            game.cover.save(fname, ContentFile(r.content), save=True)

    return game
