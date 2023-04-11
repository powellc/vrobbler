import logging
from django.utils import timezone

from imdb import Cinemagoer, helpers
from imdb.Character import IMDbParserError

imdb_client = Cinemagoer()

logger = logging.getLogger(__name__)


def lookup_video_from_imdb(name_or_id: str, kind: str = "movie") -> dict:

    # Very few video titles start with tt, but IMDB IDs often come in with it
    if name_or_id.startswith("tt"):
        name_or_id = name_or_id[2:]

    video_dict = {}
    imdb_id = None

    try:
        imdb_id = int(name_or_id)
    except ValueError:
        pass

    if imdb_id:
        imdb_result = imdb_client.get_movie(name_or_id)
        video_dict = imdb_result

    if not video_dict:
        imdb_results = imdb_client.search_movie(name_or_id)
        if len(imdb_results) > 1:
            for result in imdb_results:
                if result["kind"] == kind:
                    video_dict = result
                    break

        if len(imdb_results) == 1:
            video_dict = imdb_results[0]

    if not video_dict:
        logger.warn(f"No video found for key {name_or_id}")
        return video_dict
    imdb_client.update(video_dict)

    cover_url = video_dict.get("cover url")
    if cover_url:
        video_dict["cover url"] = helpers.resizeImage(cover_url, width=800)
    return video_dict
