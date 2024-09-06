import logging

from scrobbles.utils import convert_to_seconds
from videos.imdb import lookup_video_from_imdb
from videos.models import Series, Video
from videos.skatevideosite import lookup_video_from_skatevideosite

logger = logging.getLogger(__name__)


def get_or_create_video(data_dict: dict, post_keys: dict, force_update=False):
    name_or_id = data_dict.get(post_keys.get("IMDB_ID"), "") or data_dict.get(
        post_keys.get("VIDEO_TITLE"), ""
    )
    imdb_metadata = lookup_video_from_imdb(name_or_id)
    skatevideosite_metadata = lookup_video_from_skatevideosite(name_or_id)
    youtube_metadata = {}  # TODO lookup_video_from_youtube(name_or_id)

    video_dict = skatevideosite_metadata or youtube_metadata or imdb_metadata
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
        if not "overview" in video_dict.keys():
            video_dict["overview"] = data_dict.get(
                post_keys.get("OVERVIEW"), None
            )
        if not "tagline" in video_dict.keys():
            video_dict["tagline"] = data_dict.get(
                post_keys.get("TAGLINE"), None
            )
        if not "tmdb_id" in video_dict.keys():
            video_dict["tmdb_id"] = data_dict.get(
                post_keys.get("TMDB_ID"), None
            )

        series_name = video_dict.pop("series_name", None)
        if series_name:

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
