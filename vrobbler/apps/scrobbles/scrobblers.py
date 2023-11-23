import logging
import pendulum
from typing import Optional

from boardgames.bgg import lookup_boardgame_from_bgg
from boardgames.models import BoardGame
from books.models import Book
from books.openlibrary import lookup_book_from_openlibrary
from dateutil.parser import parse
from django.utils import timezone
from music.constants import JELLYFIN_POST_KEYS
from music.models import Track
from music.utils import (
    get_or_create_album,
    get_or_create_artist,
    get_or_create_track,
)
from podcasts.models import Episode
from scrobbles.models import Scrobble
from scrobbles.utils import convert_to_seconds, parse_mopidy_uri
from sports.models import SportEvent
from sports.thesportsdb import lookup_event_from_thesportsdb
from videogames.howlongtobeat import lookup_game_from_hltb
from videogames.models import VideoGame
from videos.models import Video
from locations.models import GeoLocation, RawGeoLocation
from vrobbler.apps.locations.constants import LOCATION_PROVIDERS

logger = logging.getLogger(__name__)


def mopidy_scrobble_podcast(
    data_dict: dict, user_id: Optional[int]
) -> Scrobble:
    mopidy_uri = data_dict.get("mopidy_uri", "")
    parsed_data = parse_mopidy_uri(mopidy_uri)

    producer_dict = {"name": data_dict.get("artist")}

    podcast_name = data_dict.get("album")
    if not podcast_name:
        podcast_name = parsed_data.get("podcast_name")
    podcast_dict = {"name": podcast_name}

    episode_name = parsed_data.get("episode_filename")
    episode_dict = {
        "title": episode_name,
        "run_time_seconds": data_dict.get("run_time"),
        "number": parsed_data.get("episode_num"),
        "pub_date": parsed_data.get("pub_date"),
        "mopidy_uri": mopidy_uri,
    }

    episode = Episode.find_or_create(podcast_dict, producer_dict, episode_dict)

    # Now we run off a scrobble
    mopidy_data = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": data_dict.get("playback_time_ticks"),
        "source": "Mopidy",
        "mopidy_status": data_dict.get("status"),
    }

    scrobble = None
    if episode:
        scrobble = Scrobble.create_or_update(episode, user_id, mopidy_data)
    return scrobble


def mopidy_scrobble_track(
    data_dict: dict, user_id: Optional[int]
) -> Optional[Scrobble]:
    artist = get_or_create_artist(
        data_dict.get("artist"),
        mbid=data_dict.get("musicbrainz_artist_id", None),
    )
    album = get_or_create_album(
        data_dict.get("album"),
        artist=artist,
        mbid=data_dict.get("musicbrainz_album_id"),
    )
    track = get_or_create_track(
        title=data_dict.get("name"),
        mbid=data_dict.get("musicbrainz_track_id"),
        artist=artist,
        album=album,
        run_time_seconds=data_dict.get("run_time"),
    )

    # Now we run off a scrobble
    playback_seconds = data_dict.get("playback_time_ticks") / 1000
    mopidy_data = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": playback_seconds,
        "source": "Mopidy",
        "mopidy_status": data_dict.get("status"),
    }

    scrobble = Scrobble.create_or_update(track, user_id, mopidy_data)

    return scrobble


def build_scrobble_dict(data_dict: dict, user_id: int) -> dict:
    jellyfin_status = "resumed"
    if data_dict.get("IsPaused"):
        jellyfin_status = "paused"
    elif data_dict.get("NotificationType") == "PlaybackStop":
        jellyfin_status = "stopped"

    playback_seconds = convert_to_seconds(
        data_dict.get("PlaybackPosition", "")
    )
    return {
        "user_id": user_id,
        "timestamp": parse(data_dict.get("UtcTimestamp")),
        "playback_position_seconds": playback_seconds,
        "source": data_dict.get("ClientName", "Vrobbler"),
        "source_id": data_dict.get("MediaSourceId"),
        "jellyfin_status": jellyfin_status,
    }


def jellyfin_scrobble_track(
    data_dict: dict, user_id: Optional[int]
) -> Optional[Scrobble]:

    null_position_on_progress = (
        data_dict.get("PlaybackPosition") == "00:00:00"
        and data_dict.get("NotificationType") == "PlaybackProgress"
    )

    # Jellyfin has some race conditions with it's webhooks, these hacks fix some of them
    if null_position_on_progress:
        logger.error("No playback position tick from Jellyfin, aborting")
        return

    artist = get_or_create_artist(
        data_dict.get(JELLYFIN_POST_KEYS["ARTIST_NAME"]),
        mbid=data_dict.get(JELLYFIN_POST_KEYS["ARTIST_MB_ID"]),
    )
    album = get_or_create_album(
        data_dict.get(JELLYFIN_POST_KEYS["ALBUM_NAME"]),
        artist=artist,
        mbid=data_dict.get(JELLYFIN_POST_KEYS["ALBUM_MB_ID"]),
    )

    run_time = convert_to_seconds(
        data_dict.get(JELLYFIN_POST_KEYS["RUN_TIME"])
    )
    track = get_or_create_track(
        title=data_dict.get("Name"),
        artist=artist,
        album=album,
        run_time_seconds=run_time,
    )

    scrobble_dict = build_scrobble_dict(data_dict, user_id)

    # A hack to make Jellyfin work more like Mopidy for music tracks
    scrobble_dict["playback_position_seconds"] = 0

    return Scrobble.create_or_update(track, user_id, scrobble_dict)


def jellyfin_scrobble_video(data_dict: dict, user_id: Optional[int]):
    video = Video.find_or_create(data_dict)

    scrobble_dict = build_scrobble_dict(data_dict, user_id)

    return Scrobble.create_or_update(video, user_id, scrobble_dict)


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
        "source_id": "Manually scrobbled from Vrobbler and looked up via IMDB",
    }

    return Scrobble.create_or_update(video, user_id, scrobble_dict)


def manual_scrobble_event(thesportsdb_id: str, user_id: int):
    data_dict = lookup_event_from_thesportsdb(thesportsdb_id)

    event = SportEvent.find_or_create(data_dict)
    scrobble_dict = build_scrobble_dict(data_dict, user_id)
    return Scrobble.create_or_update(event, user_id, scrobble_dict)


def manual_scrobble_video_game(hltb_id: str, user_id: int):
    data_dict = lookup_game_from_hltb(hltb_id)
    game = VideoGame.find_or_create(data_dict)

    scrobble_dict = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_seconds": 0,
        "source": "Vrobbler",
        "source_id": "Manually scrobbled from Vrobbler and looked up via HLTB.com",
        "long_play_complete": False,
    }

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
        "source_id": "Manually scrobbled from Vrobbler and looked up via boardgamegeek.com",
    }

    return Scrobble.create_or_update(boardgame, user_id, scrobble_dict)


def gpslogger_scrobble_location(
    data_dict: dict, user_id: Optional[int]
) -> Optional[Scrobble]:
    # Save the data coming in
    if not user_id:
        user_id = 1  # TODO fix authing the end point to get user
    raw_location = RawGeoLocation.objects.create(
        user_id=user_id,
        lat=data_dict.get("lat"),
        lon=data_dict.get("lon"),
        altitude=data_dict.get("alt"),
        speed=data_dict.get("spd"),
        timestamp=pendulum.parse(data_dict.get("time", timezone.now())),
    )

    location = GeoLocation.find_or_create(data_dict)

    # Now we run off a scrobble
    playback_seconds = 1
    extra_data = {
        "user_id": user_id,
        "timestamp": pendulum.parse(data_dict.get("time", timezone.now())),
        "playback_position_seconds": playback_seconds,
        "source": "GPSLogger",
    }

    scrobble = Scrobble.create_or_update(location, user_id, extra_data)

    provider = f"data source: {LOCATION_PROVIDERS[data_dict.get('prov')]}"
    if scrobble.notes:
        scrobble.notes = scrobble.notes + f"\n{provider}"
    else:
        scrobble.notes = provider
    scrobble.save(update_fields=["notes"])

    return scrobble
