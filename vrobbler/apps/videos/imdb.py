import logging
from django.utils import timezone

from imdb import Cinemagoer, helpers
from imdb.Character import IMDbParserError
from scrobbles.dataclasses import VideoLogData

imdb_client = Cinemagoer()

logger = logging.getLogger(__name__)


def lookup_video_from_imdb(
    name_or_id: str, kind: str = "movie"
) -> VideoLogData:

    # Very few video titles start with tt, but IMDB IDs often come in with it
    if name_or_id.startswith("tt"):
        name_or_id = name_or_id[2:]

    imdb_id = None

    try:
        imdb_id = int(name_or_id)
    except ValueError:
        pass

    video_metadata = None
    if imdb_id:
        imdb_result = imdb_client.get_movie(name_or_id)
        imdb_client.update(imdb_result, info=["plot", "synopsis", "taglines"])
        video_metadata = imdb_result

    if not video_metadata:
        imdb_results = imdb_client.search_movie(name_or_id)
        if len(imdb_results) > 1:
            for result in imdb_results:
                if result["kind"] == kind:
                    video_metadata = result
                    break

        if len(imdb_results) == 1:
            video_metadata = imdb_results[0]
        imdb_client.update(
            video_metadata, info=["plot", "synopsis", "taglines"]
        )

    if not video_metadata:
        logger.info(
            f"[lookup_video_from_imdb] no video found on imdb",
            extra={"name_or_id": name_or_id},
        )
        return video_metadata

    imdb_client.update(video_metadata)

    cover_url = video_metadata.get("cover url")
    if cover_url:
        cover_url = helpers.resizeImage(cover_url, width=800)

    from videos.models import Video

    video_type = Video.VideoType.MOVIE
    series_name = None
    if video_metadata.get("kind") == "episode":
        series_name = video_metadata.get("episode of", None).data.get(
            "title", None
        )
        video_type = Video.VideoType.TV_EPISODE

    run_time_seconds = 0
    if video_metadata.get("runtimes"):
        run_time_seconds = int(video_metadata.get("runtimes")[0]) * 60

    return {
        "title": video_metadata.get("title"),
        "imdb_id": video_metadata.get("imdbID"),
        "video_type": video_type,
        "run_time_seconds": run_time_seconds,
        "episode_number": video_metadata.get("episode", None),
        "season_number": video_metadata.get("season", None),
        "next_imdb_id": video_metadata.get("next episode", None),
        "year": video_metadata.get("year", None),
        "series_name": series_name,
        "plot": video_metadata.get("plot outline"),
        "imdb_rating": video_metadata.get("rating"),
        "cover_url": cover_url,
    }
