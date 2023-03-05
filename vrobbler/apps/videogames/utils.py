import logging
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from django.core.files.base import File

from videogames.models import VideoGame

from vrobbler.apps.videogames.igdb import lookup_game_from_igdb

logger = logging.getLogger(__name__)


def get_or_create_videogame(
    client_id: str, token: str, igdb_id: str
) -> VideoGame:
    game = None
    logger.debug(f"Looking up video game {igdb_id}")
    game_dict = lookup_game_from_igdb(client_id, token, igdb_id)

    game = VideoGame.objects.filter(igdb_id=igdb_id).first()
    if not game:
        screenshot_url = game_dict.pop("screenshot_url")
        cover_url = game_dict.pop("cover_url")

        game = VideoGame.objects.create(**game_dict)

        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(urlopen(screenshot_url).read())
        img_temp.flush()
        img_filename = f"{game.title}_{game.uuid}.jpg"
        game.screenshot.save(img_filename, File(img_temp))

        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(urlopen(cover_url).read())
        img_temp.flush()
        img_filename = f"{game.title}_{game.uuid}.jpg"
        game.cover.save(img_filename, File(img_temp))

        logger.debug(f"Created video game {game.title} ({game.igdb_id}) ")

    return game
