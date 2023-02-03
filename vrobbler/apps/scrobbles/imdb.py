import logging
from django.utils import timezone

from imdb import Cinemagoer

imdb_client = Cinemagoer()

logger = logging.getLogger(__name__)


def lookup_video_from_imdb(imdb_id: str) -> dict:

    if 'tt' not in imdb_id:
        logger.warning(f"IMDB ID should begin with 'tt' {imdb_id}")
        return

    lookup_id = imdb_id.strip('tt')
    media = imdb_client.get_movie(lookup_id)

    run_time_seconds = 60 * 60
    runtimes = media.get("runtimes")
    if runtimes:
        run_time_seconds = int(runtimes[0]) * 60

    # Ticks otherwise known as miliseconds
    run_time_ticks = run_time_seconds * 1000 * 1000

    item_type = "Movie"
    if media.get('series title'):
        item_type = "Episode"

    try:
        plot = media.get('plot')[0]
    except TypeError:
        plot = ""
    except IndexError:
        plot = ""

    logger.debug(f"Received data from IMDB: {media.__dict__}")
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
    logger.debug(f"Parsed data from IMDB data: {data_dict}")

    return data_dict
