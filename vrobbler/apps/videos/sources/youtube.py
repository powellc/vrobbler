import pendulum
from meta_yt import Video, YouTube
from videos.metadata import VideoMetadata, VideoType
import logging

logger = logging.getLogger(__name__)

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/channel/"


def lookup_video_from_youtube(youtube_id: str) -> VideoMetadata:
    from videos.models import Channel

    video_metadata = VideoMetadata(youtube_id=youtube_id)
    try:
        yt_metadata: Optional[Video] = YouTube(
            YOUTUBE_VIDEO_URL + youtube_id
        ).video
    except KeyError:
        logger.warning("Cannot access youtube, probably thinks you're a bot")
        return video_metadata

    if yt_metadata:

        if yt_metadata.channel:
            channel, _created = Channel.objects.get_or_create(
                youtube_id=yt_metadata.channel_id,
                name=yt_metadata.channel,
            )
            video_metadata.channel_id = channel.id

        video_metadata.title = yt_metadata.title
        video_metadata.run_time_seconds = yt_metadata.duration
        video_metadata.video_type = VideoType.YOUTUBE.value
        video_metadata.youtube_id = yt_metadata.video_id
        video_metadata.cover_url = yt_metadata.thumbnail
        video_metadata.genres = yt_metadata.keywords
        video_metadata.overview = yt_metadata.metadata.get("videoDetails").get(
            "shortDescription"
        )

        date_str = (
            yt_metadata.metadata.get("microformat")
            .get("playerMicroformatRenderer")
            .get("uploadDate")
        )
        if date_str:
            video_metadata.upload_date = pendulum.parse(date_str).date()
            video_metadata.year = video_metadata.upload_date.year
        return video_metadata
