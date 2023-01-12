import logging
from typing import Any
from urllib.parse import unquote

from dateutil.parser import ParserError, parse

logger = logging.getLogger(__name__)


def convert_to_seconds(run_time: str) -> int:
    """Jellyfin sends run time as 00:00:00 string. We want the run time to
    actually be in seconds so we'll convert it"""
    if ":" in run_time:
        run_time_list = run_time.split(":")
        run_time = (int(run_time_list[1]) * 60) + int(run_time_list[2])
    return int(run_time)


def parse_mopidy_uri(uri: str) -> dict:
    logger.debug(f"Parsing URI: {uri}")
    parsed_uri = uri.split('/')

    episode_str = unquote(parsed_uri.pop(-1).strip(".mp3"))
    podcast_str = unquote(parsed_uri.pop(-1))
    possible_date_str = episode_str[0:10]

    try:
        pub_date = parse(possible_date_str)
    except ParserError:
        pub_date = ""
    logger.debug(f"Found pub date {pub_date} from Mopidy URI")

    try:
        if pub_date:
            episode_num = int(episode_str.split('-')[3])
        else:
            episode_num = int(episode_str.split('-')[0])
    except IndexError:
        episode_num = None
    except ValueError:
        episode_num = None
    logger.debug(f"Found episode num {episode_num} from Mopidy URI")

    if pub_date:
        episode_str = episode_str.strip(episode_str[:11])

    if type(episode_num) is int:
        episode_num_gap = len(str(episode_num)) + 1
        episode_str = episode_str.strip(episode_str[:episode_num_gap])

    episode_str = episode_str.replace('-', ' ')
    logger.debug(f"Found episode name {episode_str} from Mopidy URI")

    return {
        'episode_filename': episode_str,
        'episode_num': episode_num,
        'podcast_name': podcast_str,
        'pub_date': pub_date,
    }
