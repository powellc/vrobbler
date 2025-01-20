import logging

from imdb import Cinemagoer, helpers
from videos.services import metadata

imdb_client = Cinemagoer()

logger = logging.getLogger(__name__)


def lookup_video_from_imdb(
    name_or_id: str, kind: str = "movie"
) -> metadata.VideoMetadata:
    from videos.models import Series

    # Very few video titles start with tt, but IMDB IDs often come in with it
    if name_or_id.startswith("tt"):
        name_or_id = name_or_id[2:]

    imdb_id = None

    try:
        imdb_id = int(name_or_id)
    except ValueError:
        pass

    video_metadata = metadata.VideoMetadata(imdb_id=imdb_id)
    imdb_data: dict = {}

    imdb_result = imdb_client.get_movie(name_or_id)
    imdb_client.update(imdb_result, info=["plot", "synopsis", "taglines"])
    imdb_data = imdb_result

    if not imdb_data:
        imdb_results = imdb_client.search_movie(name_or_id)
        if len(imdb_results) > 1:
            for result in imdb_results:
                if result["kind"] == kind:
                    imdb_data = result
                    break

        if len(imdb_results) == 1:
            imdb_data = imdb_results[0]
        imdb_client.update(
            imdb_data,
            info=["plot", "synopsis", "taglines", "next_episode", "genres"],
        )

    if not imdb_data:
        logger.info(
            f"[lookup_video_from_imdb] no video found on imdb",
            extra={"name_or_id": name_or_id},
        )
        return None

    imdb_client.update(imdb_data)

    video_metadata.cover_url = imdb_data.get("cover url")
    if video_metadata.cover_url:
        video_metadata.cover_url = helpers.resizeImage(
            video_metadata.cover_url, width=800
        )

    video_metadata.video_type = metadata.VideoType.MOVIE
    series_name = None
    if imdb_data.get("kind") == "episode":
        series_name = imdb_data.get("episode of", None).data.get("title", None)
        series, series_created = Series.objects.get_or_create(name=series_name)
        video_metadata.video_type = metadata.VideoType.TV_EPISODE
        video_metadata.series_id = series.id

    if imdb_data.get("runtimes"):
        video_metadata.run_time_seconds = (
            int(imdb_data.get("runtimes")[0]) * 60
        )

    video_metadata.title = imdb_data.get("title", "")
    video_metadata.imdb_id = imdb_data.get("imdbID")
    video_metadata.episode_number = imdb_data.get("episode", None)
    video_metadata.season_number = imdb_data.get("season", None)
    video_metadata.next_imdb_id = imdb_data.get("next episode", None)
    video_metadata.year = imdb_data.get("year", None)
    video_metadata.plot = imdb_data.get("plot outline")
    video_metadata.imdb_rating = imdb_data.get("rating")
    video_metadata.genres = imdb_data.get("genres")

    return video_metadata
