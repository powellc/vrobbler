from enum import Enum

JELLYFIN_VIDEO_ITEM_TYPES = ["Episode", "Movie"]
JELLYFIN_AUDIO_ITEM_TYPES = ["Audio"]

LONG_PLAY_MEDIA = {
    "videogames": "VideoGame",
    "books": "Book",
    "bricksets": "BrickSet",
    "tasks": "Task",
}

PLAY_AGAIN_MEDIA = {
    "videogames": "VideoGame",
    "books": "Book",
    "boardgames": "BoardGame",
    "moods": "Mood",
    "bricksets": "BrickSet",
    "trails": "Trail",
}

MEDIA_END_PADDING_SECONDS = {
    "Video": 3600,  # 60 min
}

TASK_SOURCE_URL_PATTERNS = [
    ("https://app.shortcut.com/sure/story/{id}", "Shortcut"),
    ("https://app.todoist.com/app/task/{id}", "Todoist"),
]

for task_pattern in TASK_SOURCE_URL_PATTERNS:
    task_urls = ", ".join([t[0] for t in TASK_SOURCE_URL_PATTERNS])

SCROBBLE_CONTENT_URLS = {
    "-i": "https://www.imdb.com/title/",
    "-s": "https://www.thesportsdb.com/event/",
    "-g": "https://boardgamegeek.com/boardgame/",
    "-b": "https://www.amazon.com/",
    "-t": task_urls,
}

EXCLUDE_FROM_NOW_PLAYING = ("GeoLocation",)

MANUAL_SCROBBLE_FNS = {
    "-v": "manual_scrobble_video_game",
    "-b": "manual_scrobble_book",
    "-s": "manual_scrobble_event",
    "-i": "manual_scrobble_video",
    "-g": "manual_scrobble_board_game",
    "-w": "manual_scrobble_webpage",
    "-t": "manual_scrobble_task",
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
