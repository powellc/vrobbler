import logging
from typing import Optional

from django.utils import timezone
from music.models import Track
from podcasts.models import Episode
from scrobbles.models import Scrobble
from scrobbles.utils import parse_mopidy_uri

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
        "status": data_dict.get("status"),
    }

    scrobble = None
    if episode:
        scrobble = Scrobble.create_or_update_for_podcast_episode(
            episode, user_id, mopidy_data
        )
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
        "status": data_dict.get("status"),
    }

    scrobble = None
    if track:
        # Jellyfin MB ids suck, so always overwrite with Mopidy if they're offering
        track.musicbrainz_id = data_dict.get("musicbrainz_track_id")
        track.save()
        scrobble = Scrobble.create_or_update_for_track(
            track, user_id, mopidy_data
        )
    return scrobble
