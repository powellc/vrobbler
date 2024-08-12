VARIOUS_ARTIST_DICT = {
    "name": "Various Artists",
    "theaudiodb_id": "113641",
    "musicbrainz_id": "89ad4ac3-39f7-470e-963a-56509c546377",
}

JELLYFIN_POST_KEYS = {
    "ITEM_TYPE": "ItemType",
    "RUN_TIME": "RunTime",
    "TRACK_TITLE": "Name",
    "TIMESTAMP": "UtcTimestamp",
    "YEAR": "Year",
    "PLAYBACK_POSITION_TICKS": "PlaybackPositionTicks",
    "PLAYBACK_POSITION": "PlaybackPosition",
    "ARTIST_MB_ID": "Provider_musicbrainzartist",
    "ALBUM_MB_ID": "Provider_musicbrainzalbum",
    "RELEASEGROUP_MB_ID": "Provider_musicbrainzreleasegroup",
    "TRACK_MB_ID": "Provider_musicbrainztrack",
    "ALBUM_NAME": "Album",
    "ARTIST_NAME": "Artist",
    "STATUS": "Status",
}

MOPIDY_POST_KEYS = {
    "ITEM_TYPE": None,
    "RUN_TIME": "run_time",
    "TRACK_TITLE": "name",
    "TIMESTAMP": None,
    "YEAR": None,
    "PLAYBACK_POSITION_TICKS": "playback_time_ticks",
    "ARTIST_MB_ID": "muscibrainz_artist_id",
    "ALBUM_MB_ID": "musicbrainz_album_id",
    "RELEASEGROUP_MB_ID": None,
    "TRACK_MB_ID": "musicbrainz_track_id",
    "ALBUM_NAME": "album",
    "ARTIST_NAME": "artist",
    "STATUS": "status",
}
