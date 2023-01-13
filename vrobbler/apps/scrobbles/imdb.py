import logging
from typing import Optional
from django.utils import timezone

import imdb
from videos.models import Video

imdb_client = imdb.Cinemagoer()

logger = logging.getLogger(__name__)


def lookup_video_from_imdb(imdb_id: str) -> dict:

    if 'tt' not in imdb_id:
        logger.warning(f"IMDB ID should begin with 'tt' {imdb_id}")
        return

    lookup_id = imdb_id.strip('tt')
    media = imdb_client.get_movie(lookup_id)

    run_time_seconds = int(media.get('runtimes')[0]) * 60
    # Ticks otherwise known as miliseconds
    run_time_ticks = run_time_seconds * 1000 * 1000

    item_type = Video.VideoType.MOVIE
    if media.get('series title'):
        item_type = Video.VideoType.TV_EPISODE

    try:
        plot = media.get('plot')[0]
    except TypeError:
        plot = ""
    except IndexError:
        plot = ""

    # Build a rough approximation of a Jellyfin data response
    data_dict = {
        "ItemType": item_type,
        "Name": media.get('title'),
        "Overview": plot,
        "Tagline": media.get('tagline'),
        "Year": media.get('year'),
        "Provider_imdb": imdb_id,
        "RunTime": run_time_seconds,
        "RunTimeTicks": run_time_ticks,
        "SeriesName": media.get('series title'),
        "EpisodeNumber": media.get('episode'),
        "SeasonNumber": media.get('season'),
        "PlaybackPositionTicks": 1,
        "PlaybackPosition": 1,
        "UtcTimestamp": timezone.now().strftime('%Y-%m-%d %H:%M:%S.%f%z'),
        "IsPaused": False,
        "PlayedToCompletion": False,
    }

    return data_dict
