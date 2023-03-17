from enum import Enum

JELLYFIN_VIDEO_ITEM_TYPES = ["Episode", "Movie"]
JELLYFIN_AUDIO_ITEM_TYPES = ["Audio"]

LONG_PLAY_MEDIA = {
    "videogames": "VideoGame",
    "books": "Book",
}


class AsTsvColumn(Enum):
    ARTIST_NAME = 0
    ALBUM_NAME = 1
    TRACK_NAME = 2
    TRACK_NUMBER = 3
    RUN_TIME_SECONDS = 4
    COMPLETE = 5
    TIMESTAMP = 6
    MB_ID = 7
