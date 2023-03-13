import logging

from videos.imdb import lookup_video_from_imdb
from videos.models import Series, Video
from scrobbles.utils import convert_to_seconds

logger = logging.getLogger(__name__)


def get_or_create_video(name_or_id: str, force_update=False):
    imdb_dict = lookup_video_from_imdb(name_or_id)

    if not imdb_dict:
        return

    video, video_created = Video.objects.get_or_create(
        imdb_id=imdb_dict.get("imdbID"), title=imdb_dict.get("title")
    )

    if video_created or force_update:
        video_type = Video.VideoType.MOVIE
        series = None
        if imdb_dict.get("kind") == "episode":
            series_name = imdb_dict.get("episode of").data.get("title")
            series, series_created = Series.objects.get_or_create(
                name=series_name
            )
            video_type = Video.VideoType.TV_EPISODE
            if series_created:
                series.fix_metadata()

        run_time_seconds = 0
        if imdb_dict.get("runtimes"):
            run_time_seconds = int(imdb_dict.get("runtimes")[0]) * 60
        video_dict = {
            "video_type": video_type,
            "run_time_seconds": run_time_seconds,
            "episode_number": imdb_dict.get("episode", None),
            "season_number": imdb_dict.get("season", None),
            "tv_series_id": series.id if series else None,
        }
        Video.objects.filter(pk=video.id).update(**video_dict)
        video.refresh_from_db()

        video.fix_metadata()

    return video


def get_or_create_video_from_jellyfin(jellyfin_data: dict, force_update=True):
    """Given a Jellyfin webhook payload as a dictionary, lookup the video or
    create a new one.

    """

    video, video_created = Video.objects.get_or_create(
        imdb_id=jellyfin_data.get("Provider_imdb").replace("tt", ""),
        title=jellyfin_data.get("Name"),
    )

    if video_created:
        video_type = Video.VideoType.MOVIE
        series = None
        if jellyfin_data.get("ItemType", "") == "Episode":
            series_name = jellyfin_data.get("SeriesName", "")
            series, series_created = Series.objects.get_or_create(
                name=series_name
            )
            if series_created:
                series.fix_metadata()
            video_type = Video.VideoType.TV_EPISODE

        video_dict = {
            "video_type": video_type,
            "year": jellyfin_data.get("Year", ""),
            "overview": jellyfin_data.get("Overview", None),
            "tagline": jellyfin_data.get("Tagline", None),
            "run_time_seconds": convert_to_seconds(
                jellyfin_data.get("RunTime", 0)
            ),
            "tvdb_id": jellyfin_data.get("Provider_tvdb", None),
            "tvrage_id": jellyfin_data.get("Provider_tvrage", None),
            "episode_number": jellyfin_data.get("EpisodeNumber", None),
            "season_number": jellyfin_data.get("SeasonNumber", None),
        }

        if series:
            video_dict["tv_series_id"] = series.id

        Video.objects.filter(pk=video.id).update(**video_dict)
        video.refresh_from_db()

        video.fix_metadata()

    return video
