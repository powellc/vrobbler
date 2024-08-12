import logging
import os
from urllib.parse import unquote

from dateutil.parser import ParserError, parse
from podcasts.models import PodcastEpisode

logger = logging.getLogger(__name__)

# TODO This should be configurable in settings or per deploy
PODCAST_DATE_FORMAT = "YYYY-MM-DD"


def parse_mopidy_uri(uri: str) -> dict:
    logger.debug(f"Parsing URI: {uri}")
    parsed_uri = os.path.splitext(unquote(uri))[0].split("/")

    episode_str = parsed_uri[-1]
    podcast_name = parsed_uri[-2].strip()
    episode_num = None
    episode_num_pad = 0

    try:
        # Without episode numbers the date will lead
        pub_date = parse(episode_str[0:10])
    except ParserError:
        episode_num = int(episode_str.split("-")[0])
        episode_num_pad = len(str(episode_num)) + 1

        try:
            # Beacuse we have epsiode numbers on
            pub_date = parse(
                episode_str[
                    episode_num_pad : len(PODCAST_DATE_FORMAT)
                    + episode_num_pad
                ]
            )
        except ParserError:
            pub_date = ""

    gap_to_strip = 0
    if pub_date:
        gap_to_strip += len(PODCAST_DATE_FORMAT)
    if episode_num:
        gap_to_strip += episode_num_pad

    episode_name = episode_str[gap_to_strip:].replace("-", " ").strip()

    return {
        "episode_filename": episode_name,
        "episode_num": episode_num,
        "podcast_name": podcast_name,
        "pub_date": pub_date,
    }


def get_or_create_podcast(post_data: dict):
    mopidy_uri = post_data.get("mopidy_uri", "")
    parsed_data = parse_mopidy_uri(mopidy_uri)

    producer_dict = {"name": post_data.get("artist")}

    podcast_name = post_data.get("album")
    if not podcast_name:
        podcast_name = parsed_data.get("podcast_name")
    podcast_dict = {"name": podcast_name}

    episode_name = parsed_data.get("episode_filename")
    episode_dict = {
        "title": episode_name,
        "run_time_seconds": post_data.get("run_time"),
        "number": parsed_data.get("episode_num"),
        "pub_date": parsed_data.get("pub_date"),
        "mopidy_uri": mopidy_uri,
    }

    return PodcastEpisode.find_or_create(
        podcast_dict, producer_dict, episode_dict
    )
