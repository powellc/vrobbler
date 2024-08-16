import json
import logging
from datetime import datetime
from typing import Optional

import pendulum
import pytz
from boardgames.models import BoardGame
from books.models import Book
from dateutil.parser import parse
from django.utils import timezone
from locations.constants import LOCATION_PROVIDERS
from locations.models import GeoLocation
from music.constants import JELLYFIN_POST_KEYS, MOPIDY_POST_KEYS
from music.models import Track
from music.utils import get_or_create_track
from podcasts.utils import get_or_create_podcast
from scrobbles.constants import JELLYFIN_AUDIO_ITEM_TYPES
from scrobbles.models import Scrobble
from scrobbles.utils import convert_to_seconds
from sports.models import SportEvent
from sports.thesportsdb import lookup_event_from_thesportsdb
from videogames.howlongtobeat import lookup_game_from_hltb
from videogames.models import VideoGame
from videos.models import Video
from webpages.models import WebPage

logger = logging.getLogger(__name__)


def mopidy_scrobble_media(post_data: dict, user_id: int) -> Scrobble:
    media_type = Scrobble.MediaType.TRACK
    if "podcast" in post_data.get("mopidy_uri", ""):
        media_type = Scrobble.MediaType.PODCAST_EPISODE

    logger.info(
        "[scrobblers] webhook mopidy scrobble request received",
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

    return media_obj.scrobble_for_user(
        user_id,
        source="Mopidy",
        playback_position_seconds=int(
            post_data.get("playback_time_ticks", 1) / 1000
        ),
        status=post_data.get(MOPIDY_POST_KEYS.get("STATUS"), ""),
    )


def jellyfin_scrobble_media(
    post_data: dict, user_id: int
) -> Optional[Scrobble]:
    media_type = Scrobble.MediaType.VIDEO
    if post_data.pop("ItemType", "") in JELLYFIN_AUDIO_ITEM_TYPES:
        media_type = Scrobble.MediaType.TRACK

    logger.info(
        "[jellyfin_scrobble_track] called",
        extra={
            "user_id": user_id,
            "post_data": post_data,
            "media_type": media_type,
        },
    )

    null_position_on_progress = (
        post_data.get("PlaybackPosition") == "00:00:00"
        and post_data.get("NotificationType") == "PlaybackProgress"
    )

    # Jellyfin has some race conditions with it's webhooks, these hacks fix some of them
    if null_position_on_progress:
        logger.info(
            "[jellyfin_scrobble_track] no playback position tick, aborting",
            extra={"post_data": post_data},
        )
        return

    if media_type == Scrobble.MediaType.VIDEO:
        media_obj = Video.find_or_create(post_data)
    else:
        media_obj = get_or_create_track(
            post_data, post_keys=JELLYFIN_POST_KEYS
        )

    timestamp = parse(
        post_data.get(JELLYFIN_POST_KEYS.get("TIMESTAMP"))
    ).replace(tzinfo=pytz.utc)
    playback_status = "resumed"
    if post_data.get("IsPaused"):
        playback_status = "paused"
    elif post_data.get("NotificationType") == "PlaybackStop":
        playback_status = "stopped"

    # TODO Add some logging here, maybe?

    return media_obj.scrobble_for_user(
        user_id,
        playback_position_seconds=(timezone.now() - timestamp).seconds,
        status=playback_status,
    )


def manual_scrobble_video(imdb_id: str, user_id: int):
    video = Video.find_or_create({"imdb_id": imdb_id})

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
    scrobble_dict = build_scrobble_dict(data_dict, user_id)
    return Scrobble.create_or_update(event, user_id, scrobble_dict)


def manual_scrobble_video_game(hltb_id: str, user_id: int):
    game = VideoGame.objects.filter(hltb_id=hltb_id).first()
    if not game:
        data_dict = lookup_game_from_hltb(hltb_id)
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
        "[webhook] board game scrobble request received",
        extra={
            "boardgame_id": boardgame.id,
            "user_id": user_id,
            "scrobble_dict": scrobble_dict,
            "media_type": Scrobble.MediaType.BOARD_GAME,
        },
    )

    return Scrobble.create_or_update(boardgame, user_id, scrobble_dict)


def manual_scrobble_webpage(url: str, user_id: int):
    webpage = WebPage.find_or_create({"url": url})

    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": "Vrobbler",
    }
    logger.info(
        "[webhook] webpage scrobble request received",
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
        "[webhook] gpslogger scrobble request received",
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
