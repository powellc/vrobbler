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

    video = Video.objects.filter(imdb_id=name_or_id).first()
    if video:
        return video

    imdb_metadata = lookup_video_from_imdb(name_or_id)
    # skatevideosite_metadata = lookup_video_from_skatevideosite(name_or_id)
    # youtube_metadata = {}  # TODO lookup_video_from_youtube(name_or_id)

    video_dict = imdb_metadata
    if not video_dict:
        logger.info(
            "No video found on imdb, skatevideosite or youtube, cannot scrobble",
            extra={"name_or_id": name_or_id},
        )
        return

    video = Video.get_from_imdb_id(video_dict.get("imdb_id")

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

    return video


def get_or_create_video_from_skatevideosite(title: str, force_update: bool=True):
    return
