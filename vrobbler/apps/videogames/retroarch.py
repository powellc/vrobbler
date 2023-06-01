import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional

import pytz
from dateutil.parser import ParserError, parse
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from scrobbles.utils import convert_to_seconds
from videogames.models import VideoGame
from videogames.scrapers import scrape_game_name_from_adb
from videogames.utils import get_or_create_videogame
from vrobbler.apps.scrobbles.exceptions import UserNotFound
from vrobbler.apps.videogames.exceptions import GameNotFound

logger = logging.getLogger(__name__)

User = get_user_model()


def load_game_data(directory_path: str, user_tz=None) -> dict:
    """Given a path to a directory, cycle through each found lrtl file and
    generate game data.

    Example json file as follows:

      Name: "Sonic The Hedgehog 2 (World).lrtl"

      Contents:
      {
        "version": "1.0",
        "runtime": "0:20:19",
        "last_played": "2023-05-23 15:30:15"
      }

    """
    directory = os.fsencode(directory_path)
    games = {}
    if not user_tz:
        user_tz = settings.TIME_ZONE

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if not filename.endswith("lrtl"):
            logger.info(f'Skipping "{filename}", not lrtl file')
            continue

        game_name = filename.split(".lrtl")[0].split(" (")[0]
        with open("".join([directory_path, filename])) as f:
            try:
                games[game_name] = json.load(f)
            except json.JSONDecodeError:
                logger.warn(
                    f"Could not decode JSOn for {game_name} and file {filename}"
                )
            # Convert runtime to seconds
            games[game_name]["runtime"] = convert_to_seconds(
                games[game_name]["runtime"]
            )
            # Convert last_played to datetime in user timezone
            last_played_dt = parse(games.get(game_name).get("last_played"))
            games[game_name]["last_played"] = user_tz.localize(last_played_dt)

    return games


def lookup_from_short_mame_name(game_name: str) -> Optional[VideoGame]:
    logger.info(f"Received name {game_name}")
    try:
        mame_name = scrape_game_name_from_adb(game_name)
    except GameNotFound as e:
        logger.warning(e)
        return

    if mame_name:
        logger.info(f"Found name {game_name}")
        game_name = mame_name

    return VideoGame.objects.filter(retroarch_name=game_name).first()


def import_retroarch_lrtl_files(playlog_path: str, user_id: int) -> List[dict]:
    """Given a path to Retroarch lrtl game log file data,
    gather

    For each found log file, we'll do:
        1. Look up game, create if it doesn't exist
        2. Check for existing scrobbles
        3. Create new scrobble if last_played != last_scrobble.timestamp
        4. Calculate scrobble time from runtime - last_scrobble.long_play_time
    """
    Scrobble = apps.get_model("scrobbles", "Scrobble")
    user = User.objects.filter(pk=user_id).first()
    if not user:
        logger.warning(f"User ID {user_id} is not valid, cannot scrobble")
        raise UserNotFound

    game_logs = load_game_data(
        playlog_path, pytz.timezone(user.profile.timezone)
    )
    found_game = None
    new_scrobbles = []

    for game_name, game_data in game_logs.items():
        found_game = VideoGame.objects.filter(retroarch_name=game_name).first()

        # If we didn't find by Retroarch name, check ArcadeDB
        found_game_from_adb = None
        if not found_game:
            found_game_from_adb = lookup_from_short_mame_name(game_name)

        # If we didn't find it on ADB, go to get_or_create
        if not found_game and not found_game_from_adb:
            try:
                found_game = get_or_create_videogame(game_name)
            except GameNotFound as e:
                logger.warning(f"Game not found for: {e}")
                continue

            if found_game:
                found_game.retroarch_name = game_name
                found_game.save(update_fields=["retroarch_name"])

        if not found_game:
            logger.warning(f"No game found or created for {game_name}")
            continue

        # Found a game, check if scrobble exists
        end_datetime = game_data.get("last_played")
        found_scrobble = found_game.scrobble_set.filter(
            stop_timestamp=end_datetime
        )
        if found_scrobble:
            logger.info(f"Skipping scrobble for game {found_game.id}")
            continue

        last_scrobble = found_game.scrobble_set.last()

        long_play_complete = None
        if last_scrobble:
            long_play_complete = last_scrobble.long_play_complete

        # Default to 0 for delta, but if there's an past scrobble, use that
        delta_runtime = 0
        if last_scrobble:
            delta_runtime = last_scrobble.long_play_seconds

        playback_position_seconds = game_data["runtime"] - delta_runtime
        timestamp = end_datetime - timedelta(seconds=playback_position_seconds)
        if playback_position_seconds < 30:
            logger.info(
                f"Video game {found_game.id} played for less than 30 seconds, skipping"
            )
            continue

        logger.info(f"Queued scrobble for game {found_game.id}")
        new_scrobbles.append(
            Scrobble(
                video_game_id=found_game.id,
                timestamp=timestamp,
                stop_timestamp=end_datetime,
                playback_position_seconds=playback_position_seconds,
                played_to_completion=True,
                in_progress=False,
                long_play_seconds=game_data["runtime"],
                long_play_complete=long_play_complete,
                user_id=user_id,
                source="Retroarch",
                source_id="Imported from Retroarch play log file",
                media_type=Scrobble.MediaType.VIDEO_GAME,
            )
        )
    created_scrobbles = Scrobble.objects.bulk_create(new_scrobbles)
    logger.info(f"Created {len(created_scrobbles)} scrobbles")
    return new_scrobbles
