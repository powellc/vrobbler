import logging

from videos.imdb import lookup_video_from_imdb
from videos.models import Series, Video
from scrobbles.utils import convert_to_seconds

logger = logging.getLogger(__name__)


def get_or_create_video(data_dict: dict, post_keys: dict, force_update=False):
    name_or_id = data_dict.get(post_keys.get("IMDB_ID"), "") or data_dict.get(
        post_keys.get("VIDEO_TITLE"), ""
    )
    imdb_metadata = lookup_video_from_imdb(name_or_id)
    # skatevideosite_metadata = lookup_video_from_skatevideosite(name_or_id)
    # youtube_metadata = lookup_vide_from_youtube(name_or_id)

    video_dict = imdb_metadata
    # video_metadata = imdb_metadata or skatevideosite_metadata or youtube_metadata
    if not video_dict:
        logger.info(
            "No video found on imdb, skatevideosite or youtube, cannot scrobble",
            extra={"name_or_id": name_or_id},
        )
        return

    video, video_created = Video.objects.get_or_create(
        imdb_id=video_dict.get("imdb_id"),
        title=video_dict.get("title"),
    )
    if video_created or force_update:
        series = None
        if video_dict.get("video_type") == Video.VideoType.TV_EPISODE:

            series_name = video_dict.pop("series_name")
            series, series_created = Series.objects.get_or_create(
                name=series_name
            )
            if series_created:
                series.fix_metadata()
            video_dict["tv_series_id"] = series.id

        if genres := video_dict.pop("genres", None):
            video.genre.add(*genres)

        if cover_url := video_dict.pop("cover_url", None):
            video.scrape_cover_from_url(cover_url)

        Video.objects.filter(pk=video.id).update(**video_dict)
        video.refresh_from_db()
    return video


def get_or_create_video_from_skatevideosite(title: str, force_update=True):
    ...


def get_or_create_video_from_jellyfin(jellyfin_data: dict, force_update=True):
    """Given a Jellyfin webhook payload as a dictionary, lookup the video or
    create a new one.

    """
    video, video_created = Video.objects.get_or_create(
        imdb_id=jellyfin_data.get("Provider_imdb", "").replace("tt", ""),
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
