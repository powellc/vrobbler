import logging
from typing import Optional

from dateutil.parser import parse
from django.utils import timezone
from music.constants import JELLYFIN_POST_KEYS
from music.models import Track
from podcasts.models import Episode
from scrobbles.models import Scrobble
from scrobbles.utils import convert_to_seconds, parse_mopidy_uri
from videos.models import Video
from sports.models import SportEvent

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
        "run_time_ticks": data_dict.get("run_time_ticks"),
        "run_time": data_dict.get("run_time"),
        "number": parsed_data.get("episode_num"),
        "pub_date": parsed_data.get("pub_date"),
        "mopidy_uri": mopidy_uri,
    }

    episode = Episode.find_or_create(podcast_dict, producer_dict, episode_dict)

    # Now we run off a scrobble
    mopidy_data = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_ticks": data_dict.get("playback_time_ticks"),
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
    artist_dict = {
        "name": data_dict.get("artist", None),
        "musicbrainz_id": data_dict.get("musicbrainz_artist_id", None),
    }

    album_dict = {
        "name": data_dict.get("album"),
        "musicbrainz_id": data_dict.get("musicbrainz_album_id"),
    }

    track_dict = {
        "title": data_dict.get("name"),
        "run_time_ticks": data_dict.get("run_time_ticks"),
        "run_time": data_dict.get("run_time"),
    }

    track = Track.find_or_create(artist_dict, album_dict, track_dict)

    # Now we run off a scrobble
    mopidy_data = {
        "user_id": user_id,
        "timestamp": timezone.now(),
        "playback_position_ticks": data_dict.get("playback_time_ticks"),
        "source": "Mopidy",
        "mopidy_status": data_dict.get("status"),
    }

    # Jellyfin MB ids suck, so always overwrite with Mopidy if they're offering
    track.musicbrainz_id = data_dict.get("musicbrainz_track_id")
    track.save()

    scrobble = Scrobble.create_or_update(track, user_id, mopidy_data)

    return scrobble


def build_scrobble_dict(data_dict: dict, user_id: int) -> dict:
    jellyfin_status = "resumed"
    if data_dict.get("IsPaused"):
        jellyfin_status = "paused"
    elif data_dict.get("NotificationType") == 'PlaybackStop':
        jellyfin_status = "stopped"

    playback_ticks = data_dict.get("PlaybackPositionTicks", "")
    if playback_ticks:
        playback_ticks = playback_ticks // 10000

    return {
        "user_id": user_id,
        "timestamp": parse(data_dict.get("UtcTimestamp")),
        "playback_position_ticks": playback_ticks,
        "playback_position": data_dict.get("PlaybackPosition", ""),
        "source": data_dict.get("ClientName", "Vrobbler"),
        "source_id": data_dict.get('MediaSourceId'),
        "jellyfin_status": jellyfin_status,
    }


def jellyfin_scrobble_track(
    data_dict: dict, user_id: Optional[int]
) -> Optional[Scrobble]:

    if not data_dict.get("Provider_musicbrainztrack", None):
        # TODO we should be able to look up tracks via MB rather than error out
        logger.error(
            "No MBrainz Track ID received. This is likely because all metadata is bad, not scrobbling"
        )
        return

    null_position_on_progress = (
        data_dict.get("PlaybackPosition") == "00:00:00"
        and data_dict.get("NotificationType") == "PlaybackProgress"
    )

    # Jellyfin has some race conditions with it's webhooks, these hacks fix some of them
    if not data_dict.get("PlaybackPositionTicks") or null_position_on_progress:
        logger.error("No playback position tick from Jellyfin, aborting")
        return

    artist_dict = {
        'name': data_dict.get(JELLYFIN_POST_KEYS["ARTIST_NAME"], None),
        'musicbrainz_id': data_dict.get(
            JELLYFIN_POST_KEYS["ARTIST_MB_ID"], None
        ),
    }

    album_dict = {
        "name": data_dict.get(JELLYFIN_POST_KEYS["ALBUM_NAME"], None),
        "musicbrainz_id": data_dict.get(JELLYFIN_POST_KEYS['ALBUM_MB_ID']),
    }

    # Convert ticks from Jellyfin from microseconds to nanoseconds
    # Ain't nobody got time for nanoseconds
    track_dict = {
        "title": data_dict.get("Name", ""),
        "run_time_ticks": data_dict.get(
            JELLYFIN_POST_KEYS["RUN_TIME_TICKS"], None
        )
        // 10000,
        "run_time": convert_to_seconds(
            data_dict.get(JELLYFIN_POST_KEYS["RUN_TIME"], None)
        ),
    }
    track = Track.find_or_create(artist_dict, album_dict, track_dict)

    # Prefer Mopidy MD IDs to Jellyfin, so skip if we already have one
    if not track.musicbrainz_id:
        track.musicbrainz_id = data_dict.get(
            JELLYFIN_POST_KEYS["TRACK_MB_ID"], None
        )
        track.save()

    scrobble_dict = build_scrobble_dict(data_dict, user_id)

    # A hack to make Jellyfin work more like Mopidy for music tracks
    scrobble_dict["playback_position_ticks"] = 0
    scrobble_dict["playback_position"] = ""

    return Scrobble.create_or_update(track, user_id, scrobble_dict)


def jellyfin_scrobble_video(data_dict: dict, user_id: Optional[int]):
    if not data_dict.get("Provider_imdb", None):
        logger.error(
            "No IMDB ID received. This is likely because all metadata is bad, not scrobbling"
        )
        return
    video = Video.find_or_create(data_dict)

    scrobble_dict = build_scrobble_dict(data_dict, user_id)

    return Scrobble.create_or_update(video, user_id, scrobble_dict)


def manual_scrobble_video(data_dict: dict, user_id: Optional[int]):
    if not data_dict.get("Provider_imdb", None):
        logger.error(
            "No IMDB ID received. This is likely because all metadata is bad, not scrobbling"
        )
        return
    video = Video.find_or_create(data_dict)

    scrobble_dict = build_scrobble_dict(data_dict, user_id)

    return Scrobble.create_or_update(video, user_id, scrobble_dict)


def manual_scrobble_event(data_dict: dict, user_id: Optional[int]):
    if not data_dict.get("Provider_thesportsdb", None):
        logger.error(
            "No TheSportsDB ID received. This is likely because all metadata is bad, not scrobbling"
        )
        return
    event = SportEvent.find_or_create(data_dict)

    scrobble_dict = build_scrobble_dict(data_dict, user_id)

    return Scrobble.create_or_update(event, user_id, scrobble_dict)
