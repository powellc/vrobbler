from enum import Enum
from typing import Optional


YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="
IMDB_VIDEO_URL = "https://www.imdb.com/title/tt"


class VideoType(Enum):
    UNKNOWN = "U"
    TV_EPISODE = "E"
    MOVIE = "M"
    SKATE_VIDEO = "S"
    YOUTUBE = "Y"

    @classmethod
    def as_choices(cls) -> tuple:
        return tuple((i.name, i.value) for i in cls)


class VideoMetadata:
    title: str
    video_type: VideoType = VideoType.UNKNOWN
    run_time_seconds: int = (
        60  # Silly default, but things break if this is 0 or null
    )
    imdb_id: Optional[str]
    youtube_id: Optional[str]

    # IMDB specific
    episode_number: Optional[str]
    season_number: Optional[str]
    next_imdb_id: Optional[str]
    year: Optional[int]
    tv_series_id: Optional[int]
    plot: Optional[str]
    imdb_rating: Optional[str]
    cover_url: Optional[str]
    overview: Optional[str]

    # YouTube specific
    channel_id: Optional[int]

    # General
    cover_url: Optional[str]
    genres: list[str]

    def __init__(
        self,
        imdb_id: Optional[str] = "",
        youtube_id: Optional[str] = "",
        run_time_seconds: int = 900,
    ):
        self.imdb_id = imdb_id
        self.youtube_id = youtube_id
        self.run_time_seconds = run_time_seconds

    def as_dict_with_cover_and_genres(self) -> tuple:
        video_dict = vars(self)
        cover = video_dict.pop("cover_url")
        genres = video_dict.pop("genres")
        return video_dict, cover, genres
