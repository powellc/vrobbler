import json
import logging

import pendulum
import requests
from django.conf import settings

from videos.metadata import VideoMetadata, VideoType

logger = logging.getLogger(__name__)

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/channel/"

API_KEY = settings.GOOGLE_API_KEY
GOOGLE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={youtube_id}&key={key}"


def lookup_video_from_youtube(youtube_id: str) -> VideoMetadata:
    from videos.models import Channel

    video_metadata = VideoMetadata(youtube_id=youtube_id)

    url = GOOGLE_VIDEOS_URL.format(youtube_id=youtube_id, key=API_KEY)
    headers = {"User-Agent": "Vrobbler 0.11.12"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.warning(
            "Bad response from Google", extra={"response": response}
        )
        return video_metadata

    yt_metadata = (
        json.loads(response.content).get("items", [None])[0].get("snippet")
    )
    duration_iso8601 = (
        json.loads(response.content)
        .get("items", [None])[0]
        .get("contentDetails", {})
        .get("duration")
    )
    minutes = duration_iso8601.split("PT")[1].split("M")[0]
    seconds = duration_iso8601.split("PT")[1].split("M")[1].replace("S", "")

    duration = (int(minutes) * 60) + int(seconds)

    if yt_metadata:
        if yt_metadata.get("channelId"):
            channel, _ = Channel.objects.get_or_create(
                youtube_id=yt_metadata.get("channelId"),
                name=yt_metadata.get("channelTitle"),
            )
            video_metadata.channel_id = channel.id

        video_metadata.title = yt_metadata.get("title", "")
        video_metadata.run_time_seconds = duration
        video_metadata.video_type = VideoType.YOUTUBE.value
        video_metadata.youtube_id = youtube_id
        video_metadata.cover_url = (
            yt_metadata.get("thumbnails", {}).get("high", {}).get("url", {})
        )
        video_metadata.genres = yt_metadata.get("tags")
        video_metadata.overview = yt_metadata.get("description")

        date_str = yt_metadata.get("publishedAt")
        if date_str:
            video_metadata.upload_date = pendulum.parse(date_str).date()
            video_metadata.year = video_metadata.upload_date.year
        return video_metadata
