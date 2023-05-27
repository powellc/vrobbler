import json
import logging
import os
from datetime import datetime, timedelta
from typing import List

import pytz
from dateutil.parser import ParserError, parse
from django.apps import apps

from vrobbler.apps.scrobbles.utils import convert_to_seconds
from vrobbler.apps.videogames.scrapers import scrape_game_name_from_adb
from vrobbler.apps.videogames.utils import get_or_create_videogame

logger = logging.getLogger(__name__)

from videogames.models import VideoGame


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
        user_tz = pytz.utc

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if not filename.endswith("lrtl"):
            logger.info(
                f"Found non-gamelog file extension, skipping {filename}"
            )
            continue

        game_name = filename.split(".lrtl")[0].split(" (")[0]
        with open("".join([directory_path, filename])) as f:
            games[game_name] = json.load(f)
            # Convert runtime to seconds
            games[game_name]["runtime"] = convert_to_seconds(
                games[game_name]["runtime"]
            )
            # Convert last_played to datetime in user timezone
            games[game_name]["last_played"] = parse(
                games[game_name]["last_played"]
            ).replace(tzinfo=user_tz)

    return games


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

    game_logs = load_game_data(playlog_path)
    found_game = None
    new_scrobbles = []

    for game_name, game_data in game_logs.items():
        # Use the retroarch name, because we can't change those but may want to
        # tweak the found game
        mame_name = scrape_game_name_from_adb(game_name)
        if mame_name:
            game_name = mame_name

        found_game = VideoGame.objects.filter(retroarch_name=game_name).first()

        if not found_game:
            found_game = get_or_create_videogame(game_name)
            if found_game:
                found_game.retroarch_name = game_name
                found_game.save(update_fields=["retroarch_name"])

        if found_game:
            found_scrobble = found_game.scrobble_set.filter(
                stop_timestamp=game_data["last_played"]
            )
            if found_scrobble:
                logger.info(
                    f"Found scrobble for {game_name} with stop_timestamp {game_data['last_played']}, not scrobbling"
                )
                continue
            last_scrobble = found_game.scrobble_set.last()

            delta_runtime = 0
            if last_scrobble:
                delta_runtime = last_scrobble.long_play_seconds

            playback_position_seconds = game_data["runtime"] - delta_runtime

            timestamp = game_data["last_played"] + timedelta(
                seconds=playback_position_seconds
            )

            if playback_position_seconds < 30:
                logger.info(
                    f"Video game {found_game.id} played for less than 30 seconds, skipping"
                )
            new_scrobbles.append(
                Scrobble(
                    video_game_id=found_game.id,
                    timestamp=timestamp,
                    stop_timestamp=game_data["last_played"],
                    playback_position_seconds=playback_position_seconds,
                    played_to_completion=True,
                    in_progress=False,
                    long_play_seconds=game_data["runtime"],
                    user_id=user_id,
                    source="Retroarch",
                    source_id="Imported from Retroarch play log file",
                    media_type=Scrobble.MediaType.VIDEO_GAME,
                )
            )
    created_scrobbles = Scrobble.objects.bulk_create(new_scrobbles)
    return new_scrobbles
