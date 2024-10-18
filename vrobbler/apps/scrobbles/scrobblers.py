import re
import logging
from typing import Optional

import pendulum
import pytz
from boardgames.models import BoardGame
from books.models import Book
from dateutil.parser import parse
from django.conf import settings
from django.utils import timezone
from locations.constants import LOCATION_PROVIDERS
from locations.models import GeoLocation
from music.constants import JELLYFIN_POST_KEYS, MOPIDY_POST_KEYS
from music.models import Track
from music.utils import get_or_create_track
from podcasts.utils import get_or_create_podcast
from scrobbles.constants import JELLYFIN_AUDIO_ITEM_TYPES
from scrobbles.models import Scrobble
from sports.models import SportEvent
from sports.thesportsdb import lookup_event_from_thesportsdb
from videogames.howlongtobeat import lookup_game_from_hltb
from videogames.models import VideoGame
from videos.models import Video
from scrobbles.constants import (
    MANUAL_SCROBBLE_FNS,
    SCROBBLE_CONTENT_URLS,
)
from tasks.models import Task
from vrobbler.apps.tasks.constants import (
    TODOIST_TITLE_PREFIX_LABELS,
    TODOIST_TITLE_SUFFIX_LABELS,
)
from webpages.models import WebPage

logger = logging.getLogger(__name__)


def mopidy_scrobble_media(post_data: dict, user_id: int) -> Scrobble:
    media_type = Scrobble.MediaType.TRACK
    if "podcast" in post_data.get("mopidy_uri", ""):
        media_type = Scrobble.MediaType.PODCAST_EPISODE

    logger.info(
        "[mopidy_webhook] called",
        extra={
            "user_id": user_id,
            "post_data": post_data,
            "media_type": media_type,
        },
    )

    if media_type == Scrobble.MediaType.PODCAST_EPISODE:
        media_obj = get_or_create_podcast(post_data)
    else:
        media_obj = get_or_create_track(post_data, MOPIDY_POST_KEYS)

    log = {}
    try:
        log = {"mopidy_source": post_data.get("mopidy_uri", "").split(":")[0]}
    except IndexError:
        pass

    return media_obj.scrobble_for_user(
        user_id,
        source="Mopidy",
        playback_position_seconds=int(
            post_data.get(MOPIDY_POST_KEYS.get("PLAYBACK_POSITION_TICKS"), 1)
            / 1000
        ),
        status=post_data.get(MOPIDY_POST_KEYS.get("STATUS"), ""),
        log=log,
    )


def jellyfin_scrobble_media(
    post_data: dict, user_id: int
) -> Optional[Scrobble]:
    media_type = Scrobble.MediaType.VIDEO
    if post_data.pop("ItemType", "") in JELLYFIN_AUDIO_ITEM_TYPES:
        media_type = Scrobble.MediaType.TRACK

    null_position_on_progress = (
        post_data.get("PlaybackPosition") == "00:00:00"
        and post_data.get("NotificationType") == "PlaybackProgress"
    )

    # Jellyfin has some race conditions with it's webhooks, these hacks fix some of them
    if null_position_on_progress:
        logger.info(
            "[jellyfin_scrobble_media] no playback position tick, aborting",
            extra={"post_data": post_data},
        )
        return

    timestamp = parse(
        post_data.get(JELLYFIN_POST_KEYS.get("TIMESTAMP"), "")
    ).replace(tzinfo=pytz.utc)

    playback_position_seconds = int(
        post_data.get(JELLYFIN_POST_KEYS.get("PLAYBACK_POSITION_TICKS"), 1)
        / 10000000
    )
    if media_type == Scrobble.MediaType.VIDEO:
        media_obj = Video.find_or_create(post_data)
    else:
        media_obj = get_or_create_track(
            post_data, post_keys=JELLYFIN_POST_KEYS
        )
        # A hack because we don't worry about updating music ... we either finish it or we don't
        playback_position_seconds = 0

    if not media_obj:
        logger.info(
            "[jellyfin_scrobble_media] no video found from POST data",
            extra={"post_data": post_data},
        )
        return

    playback_status = "resumed"
    if post_data.get("IsPaused"):
        playback_status = "paused"
    elif post_data.get("NotificationType") == "PlaybackStop":
        playback_status = "stopped"

    return media_obj.scrobble_for_user(
        user_id,
        source=post_data.get(JELLYFIN_POST_KEYS.get("SOURCE")),
        playback_position_seconds=playback_position_seconds,
        status=playback_status,
    )


def manual_scrobble_video(imdb_id: str, user_id: int):
    if "tt" not in imdb_id:
        imdb_id = "tt" + imdb_id

    video = Video.find_or_create({JELLYFIN_POST_KEYS.get("IMDB_ID"): imdb_id})

    # When manually scrobbling, try finding a source from the series
    source = "Vrobbler"
    if video.tv_series:
        source = video.tv_series.preferred_source
    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": source,
    }

    logger.info(
        "[scrobblers] manual video scrobble request received",
        extra={
            "video_id": video.id,
            "user_id": user_id,
            "scrobble_dict": scrobble_dict,
            "media_type": Scrobble.MediaType.VIDEO,
        },
    )

    return Scrobble.create_or_update(video, user_id, scrobble_dict)


def manual_scrobble_event(thesportsdb_id: str, user_id: int):
    data_dict = lookup_event_from_thesportsdb(thesportsdb_id)

    event = SportEvent.find_or_create(data_dict)
    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": "TheSportsDB",
    }
    return Scrobble.create_or_update(event, user_id, scrobble_dict)


def manual_scrobble_video_game(hltb_id: str, user_id: int):
    game = VideoGame.objects.filter(hltb_id=hltb_id).first()
    if not game:
        data_dict = lookup_game_from_hltb(hltb_id)
        if not data_dict:
            logger.info(
                "[manual_scrobble_video_game] game not found on hltb",
                extra={
                    "hltb_id": hltb_id,
                    "user_id": user_id,
                    "media_type": Scrobble.MediaType.VIDEO_GAME,
                },
            )
            return

        game = VideoGame.find_or_create(data_dict)

    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": "Vrobbler",
        "long_play_complete": False,
    }

    logger.info(
        "[scrobblers] manual video game scrobble request received",
        extra={
            "videogame_id": game.id,
            "user_id": user_id,
            "scrobble_dict": scrobble_dict,
            "media_type": Scrobble.MediaType.VIDEO_GAME,
        },
    )

    return Scrobble.create_or_update(game, user_id, scrobble_dict)


def manual_scrobble_book(openlibrary_id: str, user_id: int):
    book = Book.find_or_create(openlibrary_id)

    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": "Vrobbler",
        "long_play_complete": False,
    }

    logger.info(
        "[scrobblers] manual book scrobble request received",
        extra={
            "book_id": book.id,
            "user_id": user_id,
            "scrobble_dict": scrobble_dict,
            "media_type": Scrobble.MediaType.BOOK,
        },
    )

    return Scrobble.create_or_update(book, user_id, scrobble_dict)


def manual_scrobble_board_game(bggeek_id: str, user_id: int):
    boardgame = BoardGame.find_or_create(bggeek_id)

    if not boardgame:
        logger.error(f"No board game found for ID {bggeek_id}")
        return

    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": "Vrobbler",
    }
    logger.info(
        "[vrobbler-scrobble] board game scrobble request received",
        extra={
            "boardgame_id": boardgame.id,
            "user_id": user_id,
            "scrobble_dict": scrobble_dict,
            "media_type": Scrobble.MediaType.BOARD_GAME,
        },
    )

    return Scrobble.create_or_update(boardgame, user_id, scrobble_dict)


def manual_scrobble_from_url(url: str, user_id: int) -> Scrobble:
    """We have scrobblable media URLs, and then any other webpages that
    we want to scrobble as a media type in and of itself. This checks whether
    we know about the content type, and routes it to the appropriate media
    scrobbler. Otherwise, return nothing."""
    content_key = ""
    try:
        domain = url.split("//")[-1].split("/")[0]
    except IndexError:
        domain = None

    for key, content_url in SCROBBLE_CONTENT_URLS.items():
        if domain in content_url:
            content_key = key

    item_id = None
    if not content_key:
        content_key = "-w"
        item_id = url

    if not item_id:
        try:
            item_id = re.findall("\d+", url)[0]
        except IndexError:
            pass

    if content_key == "-t":
        item_id = url

    scrobble_fn = MANUAL_SCROBBLE_FNS[content_key]
    return eval(scrobble_fn)(item_id, user_id)


def todoist_scrobble_task_finish(
    todoist_task: dict, user_id: int
) -> Optional[Scrobble]:
    scrobble = Scrobble.objects.filter(
        user_id=user_id, log__todoist_id=todoist_task.get("todoist_id")
    ).first()

    if not scrobble:
        logger.info(
            "[todoist_scrobble_task_finish] todoist webhook finish called on missing task"
        )
        return

    if not scrobble.in_progress or scrobble.played_to_completion:
        logger.info(
            "[todoist_scrobble_task_finish] todoist webhook finish called on finished task"
        )
        return

    scrobble.stop(force_finish=True)

    return scrobble


def todoist_scrobble_task(todoist_task: dict, user_id: int) -> Scrobble:

    prefix = ""
    suffix = ""
    for label in todoist_task["todoist_label_list"]:
        if label in TODOIST_TITLE_PREFIX_LABELS:
            prefix = label
        if label in TODOIST_TITLE_SUFFIX_LABELS:
            suffix = label

    if not prefix and suffix:
        logger.warning(
            "Missing a prefix and suffix tag for task",
            extra={"todoist_scrobble_task": todoist_task},
        )

    title = " ".join([prefix.capitalize(), suffix.capitalize()])

    task = Task.find_or_create(title)

    in_progress_scrobble = Scrobble.objects.filter(
        in_progress=True,
        log__todoist_id=todoist_task.get("todoist_id"),
        task=task,
    ).last()
    in_progress_in_todoist = (
        "inprogress" in todoist_task["todoist_label_list"]
    )
    if not in_progress_scrobble and not in_progress_in_todoist:
        logger.info(
            "[todoist_scrobble_task] no task in progress, and no inprogress label found",
            extra={
                "todoist_type": todoist_task["todoist_type"],
                "todoist_event": todoist_task["todoist_event"],
                "todoist_id": todoist_task["todoist_id"],
            },
        )
        return 

    if in_progress_scrobble and not in_progress_in_todoist:
        scrobble = todoist_scrobble_task_finish(todoist_task, user_id)

    # TODO this logic probably belongs in create_or_update
    if in_progress_scrobble:
        return scrobble

    # TODO Should use updated_at from TOdoist, but parsing isn't working
    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": "Todoist",
        "log": todoist_task,
    }

    logger.info(
        "[todoist_scrobble_task] task scrobble request received",
        extra={
            "task_id": task.id,
            "user_id": user_id,
            "scrobble_dict": scrobble_dict,
            "media_type": Scrobble.MediaType.TASK,
        },
    )
    scrobble = Scrobble.create_or_update(task, user_id, scrobble_dict)
    return scrobble


def manual_scrobble_task(url: str, user_id: int):
    source_id = re.findall("\d+", url)[0]

    if "todoist" in url:
        source = "Todoist"
        title = "Generic Todoist task"
        description = " ".join(url.split("/")[-1].split("-")[:-1]).capitalize()

    task = Task.find_or_create(title)

    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": source,
        "log": {"description": description, "source_id": source_id},
    }
    logger.info(
        "[vrobbler-scrobble] webpage scrobble request received",
        extra={
            "task_id": task.id,
            "user_id": user_id,
            "scrobble_dict": scrobble_dict,
            "media_type": Scrobble.MediaType.WEBPAGE,
        },
    )
    scrobble = Scrobble.create_or_update(task, user_id, scrobble_dict)
    return scrobble


def manual_scrobble_webpage(url: str, user_id: int):
    webpage = WebPage.find_or_create({"url": url})

    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": "Vrobbler",
    }
    logger.info(
        "[vrobbler-scrobble] webpage scrobble request received",
        extra={
            "webpage_id": webpage.id,
            "user_id": user_id,
            "scrobble_dict": scrobble_dict,
            "media_type": Scrobble.MediaType.WEBPAGE,
        },
    )

    scrobble = Scrobble.create_or_update(webpage, user_id, scrobble_dict)
    # possibly async this?
    scrobble.push_to_archivebox()
    return scrobble


def gpslogger_scrobble_location(data_dict: dict, user_id: int) -> Scrobble:
    location = GeoLocation.find_or_create(data_dict)

    timestamp = pendulum.parse(data_dict.get("time", timezone.now()))
    extra_data = {
        "user_id": user_id,
        "timestamp": timestamp,
        "source": "GPSLogger",
        "media_type": Scrobble.MediaType.GEO_LOCATION,
    }

    scrobble = Scrobble.create_or_update_location(
        location,
        extra_data,
        user_id,
    )

    provider = LOCATION_PROVIDERS[data_dict.get("prov")]

    if "gps_updates" not in scrobble.log.keys():
        scrobble.log["gps_updates"] = []

    scrobble.log["gps_updates"].append(
        {
            "timestamp": data_dict.get("time"),
            "position_provider": provider,
        }
    )
    if scrobble.timestamp:
        scrobble.playback_position_seconds = (
            timezone.now() - scrobble.timestamp
        ).seconds

    scrobble.save(update_fields=["log", "playback_position_seconds"])
    logger.info(
        "[gpslogger_webhook] gpslogger scrobble request received",
        extra={
            "scrobble_id": scrobble.id,
            "provider": provider,
            "user_id": user_id,
            "timestamp": extra_data.get("timestamp"),
            "raw_timestamp": data_dict.get("time"),
            "media_type": Scrobble.MediaType.GEO_LOCATION,
        },
    )

    return scrobble


def web_scrobbler_scrobble_video_or_song(
    data_dict: dict, user_id: Optional[int]
) -> Scrobble:
    # We're not going to create music tracks, because the only time
    # we'd hit this is if we're listening to a concert or something.
    artist_name = data_dict.get("artist")
    track_name = data_dict.get("track")
    tracks = Track.objects.filter(
        artist__name=data_dict.get("artist"), title=data_dict.get("track")
    )
    if tracks.count() > 1:
        logger.warning(
            "Multiple tracks found for Web Scrobbler",
            extra={"artist": artist_name, "track": track_name},
        )
    track = tracks.first()

    # No track found, create a Video
    if not track:
        Video.find_or_create(data_dict)

    # Now we run off a scrobble
    mopidy_data = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": data_dict.get("playback_time_ticks"),
        "source": "Mopidy",
        "mopidy_status": data_dict.get("status"),
    }

    logger.info(
        "[scrobblers] webhook mopidy scrobble request received",
        extra={
            "episode_id": episode.id if episode else None,
            "user_id": user_id,
            "scrobble_dict": mopidy_data,
            "media_type": Scrobble.MediaType.PODCAST_EPISODE,
        },
    )

    scrobble = None
    if episode:
        scrobble = Scrobble.create_or_update(episode, user_id, mopidy_data)
    return scrobble
