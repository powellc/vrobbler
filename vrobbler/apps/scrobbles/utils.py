import logging
from urllib.parse import unquote

from django.contrib.auth import get_user_model

from dateutil.parser import ParserError, parse
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)
User = get_user_model()


def convert_to_seconds(run_time: str) -> int:
    """Jellyfin sends run time as 00:00:00 string. We want the run time to
    actually be in seconds so we'll convert it"

    This is actually deprecated, as we now convert to seconds before saving.
    But for older videos, we'll leave this here.
    """
    if ":" in str(run_time):
        run_time_list = run_time.split(":")
        hours = int(run_time_list[0])
        minutes = int(run_time_list[1])
        seconds = int(run_time_list[2])
        run_time = (((hours * 60) + minutes) * 60) + seconds
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


def check_scrobble_for_finish(
    scrobble: "Scrobble", force_to_100=False, force_finish=False
) -> None:
    completion_percent = scrobble.media_obj.COMPLETION_PERCENT

    if scrobble.percent_played >= completion_percent or force_finish:
        logger.info(f"{scrobble.id} {completion_percent} met, finishing")

        if (
            scrobble.playback_position_ticks
            and scrobble.media_obj.run_time_ticks
            and force_to_100
        ):
            scrobble.playback_position_ticks = (
                scrobble.media_obj.run_time_ticks
            )
            logger.info(
                f"{scrobble.playback_position_ticks} set to {scrobble.media_obj.run_time_ticks}"
            )

        scrobble.in_progress = False
        scrobble.is_paused = False
        scrobble.played_to_completion = True

        scrobble.save(
            update_fields=[
                "in_progress",
                "is_paused",
                "played_to_completion",
                'playback_position_ticks',
            ]
        )

    if scrobble.percent_played % 5 == 0:
        if getattr(settings, "KEEP_DETAILED_SCROBBLE_LOGS", False):
            scrobble.scrobble_log += f"\n{str(scrobble.timestamp)} - {scrobble.playback_position} - {str(scrobble.playback_position_ticks)} - {str(scrobble.percent_played)}%"
            scrobble.save(update_fields=['scrobble_log'])


def get_scrobbles_for_media(media_obj, user: User) -> models.QuerySet:
    from scrobbles.models import Scrobble

    if media_obj.__class__.__name__ == 'Book':
        media_query = models.Q(book=media_obj)
    return Scrobble.objects.filter(media_query, user=user)
