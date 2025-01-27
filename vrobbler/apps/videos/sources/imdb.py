import logging

from imdb import Cinemagoer, helpers
from videos.metadata import VideoMetadata, VideoType

imdb_client = Cinemagoer()

logger = logging.getLogger(__name__)


def lookup_video_from_imdb(
    name_or_id: str, kind: str = "movie"
) -> VideoMetadata:
    from videos.models import Series

    # Very few video titles start with tt, but IMDB IDs often come in with it
    if name_or_id.startswith("tt"):
        name_or_id = name_or_id[2:]

    imdb_id = None

    try:
        imdb_id = int(name_or_id)
    except ValueError:
        pass

    video_metadata = VideoMetadata(imdb_id=imdb_id)
    imdb_result: dict = {}

    imdb_result = imdb_client.get_movie(name_or_id)

    if not imdb_result:
        imdb_result = {}
        imdb_results: list = imdb_client.search_movie(name_or_id)
        if len(imdb_results) > 1:
            for result in imdb_results:
                if result["kind"] == kind:
                    imdb_client.update(
                        result,
                        info=[
                            "plot",
                            "synopsis",
                            "taglines",
                            "next_episode",
                            "genres",
                        ],
                    )
                    imdb_result = result
                    break

        if len(imdb_results) == 1:
            imdb_result = imdb_results[0]

        imdb_client.update(
            imdb_result,
            info=["plot", "synopsis", "taglines", "next_episode", "genres"],
        )

    if not imdb_result:
        logger.info(
            f"[lookup_video_from_imdb] no video found on imdb",
            extra={"name_or_id": name_or_id},
        )
        return None

    video_metadata.cover_url = imdb_result.get("cover url")
    if video_metadata.cover_url:
        video_metadata.cover_url = helpers.resizeImage(
            video_metadata.cover_url, width=800
        )

    video_metadata.video_type = VideoType.MOVIE
    series_name = None
    if imdb_result.get("kind") == "episode":
        series_name = imdb_result.get("episode of", None).data.get(
            "title", None
        )
        series, _ = Series.objects.get_or_create(name=series_name)
        video_metadata.video_type = VideoType.TV_EPISODE
        video_metadata.tv_series_id = series.id

    if imdb_result.get("runtimes"):
        video_metadata.run_time_seconds = (
            int(imdb_result.get("runtimes")[0]) * 60
        )

    video_metadata.title = imdb_result.get("title", "")
    video_metadata.imdb_id = imdb_result.get("imdbID")
    video_metadata.episode_number = imdb_result.get("episode", None)
    video_metadata.season_number = imdb_result.get("season", None)
    video_metadata.next_imdb_id = imdb_result.get("next episode", None)
    video_metadata.year = imdb_result.get("year", None)
    video_metadata.plot = imdb_result.get("plot outline")
    video_metadata.imdb_rating = imdb_result.get("rating")
    video_metadata.genres = imdb_result.get("genres")

    return video_metadata
