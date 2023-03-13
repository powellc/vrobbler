import logging
from urllib.parse import unquote

from dateutil.parser import ParserError, parse
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from vrobbler.apps.profiles.utils import now_user_timezone

from vrobbler.apps.scrobbles.constants import LONG_PLAY_MEDIA

logger = logging.getLogger(__name__)
User = get_user_model()


def convert_to_seconds(run_time: str) -> int:
    """Jellyfin sends run time as 00:00:00 string. We want the run time to
    actually be in seconds so we'll convert it"

    This is actually deprecated, as we now convert to seconds before saving.
    But for older videos, we'll leave this here.
    """
    run_time_int = 0
    if ":" in str(run_time):
        run_time_list = run_time.split(":")
        hours = int(run_time_list[0])
        minutes = int(run_time_list[1])
        seconds = int(run_time_list[2])
        run_time_int = int((((hours * 60) + minutes) * 60) + seconds)
    return run_time_int


def parse_mopidy_uri(uri: str) -> dict:
    logger.debug(f"Parsing URI: {uri}")
    parsed_uri = uri.split("/")

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
            episode_num = int(episode_str.split("-")[3])
        else:
            episode_num = int(episode_str.split("-")[0])
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

    episode_str = episode_str.replace("-", " ")
    logger.debug(f"Found episode name {episode_str} from Mopidy URI")

    return {
        "episode_filename": episode_str,
        "episode_num": episode_num,
        "podcast_name": podcast_str,
        "pub_date": pub_date,
    }


def check_scrobble_for_finish(
    scrobble: "Scrobble", force_to_100=False, force_finish=False
) -> None:
    completion_percent = scrobble.media_obj.COMPLETION_PERCENT

    if scrobble.percent_played >= completion_percent or force_finish:
        if (
            scrobble.playback_position_seconds
            and scrobble.media_obj.run_time_seconds
        ):
            logger.info(f"{scrobble.id} {completion_percent} met, finishing")
            scrobble.playback_position_seconds = (
                scrobble.media_obj.run_time_seconds
            )
            logger.info(
                f"{scrobble.playback_position_seconds} set to {scrobble.media_obj.run_time_seconds}"
            )

        scrobble.in_progress = False
        scrobble.is_paused = False
        scrobble.played_to_completion = True

        scrobble.save(
            update_fields=[
                "in_progress",
                "is_paused",
                "played_to_completion",
                "playback_position_seconds",
            ]
        )


def get_scrobbles_for_media(media_obj, user: User) -> models.QuerySet:
    Scrobble = apps.get_model(app_label="scrobbles", model_name="Scrobble")

    media_query = None
    media_class = media_obj.__class__.__name__
    if media_class == "Book":
        media_query = models.Q(book=media_obj)
    if media_class == "VideoGame":
        media_query = models.Q(video_game=media_obj)

    if not media_query:
        logger.warn("Do not know about media {media_class} 🙍")
        return []
    return Scrobble.objects.filter(media_query, user=user)


def get_long_plays_in_progress(user: User) -> dict:
    """Find all books where the last scrobble is not marked complete"""
    media_dict = {
        "active": [],
        "inactive": [],
    }
    now = now_user_timezone(user.profile)
    for app, model in LONG_PLAY_MEDIA.items():
        media_obj = apps.get_model(app_label=app, model_name=model)
        for media in media_obj.objects.all():
            last_scrobble = media.scrobble_set.filter(user=user).last()
            if last_scrobble and last_scrobble.long_play_complete == False:
                days_past = (now - last_scrobble.timestamp).days
                if days_past > 7:
                    media_dict["inactive"].append(media)
                else:
                    media_dict["active"].append(media)
    media_dict["active"].reverse()
    media_dict["inactive"].reverse()
    return media_dict


def get_long_plays_completed(user: User) -> list:
    """Find all books where the last scrobble is not marked complete"""
    media_list = []
    for app, model in LONG_PLAY_MEDIA.items():
        media_obj = apps.get_model(app_label=app, model_name=model)
        for media in media_obj.objects.all():
            if (
                media.scrobble_set.all()
                and media.scrobble_set.filter(user=user)
                .last()
                .long_play_complete
                == True
            ):
                media_list.append(media)
    return media_list
