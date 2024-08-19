import logging
import re
from typing import Optional

from music.musicbrainz import (
    lookup_album_dict_from_mb,
    lookup_artist_from_mb,
    lookup_track_from_mb,
)
from music.constants import VARIOUS_ARTIST_DICT
from scrobbles.utils import convert_to_seconds

logger = logging.getLogger(__name__)


from music.models import Album, Artist, Track


def get_or_create_artist(name: str, mbid: str = None) -> Artist:
    artist = None

    if "feat." in name.lower():
        name = re.split("feat.", name, flags=re.IGNORECASE)[0].strip()
    if "featuring" in name.lower():
        name = re.split("featuring", name, flags=re.IGNORECASE)[0].strip()
    if "&" in name.lower():
        name = re.split("&", name, flags=re.IGNORECASE)[0].strip()

    artist_dict = lookup_artist_from_mb(name)
    mbid = mbid or artist_dict.get("id", None)

    if mbid:
        artist = Artist.objects.filter(musicbrainz_id=mbid).first()
    if not artist:
        artist = Artist.objects.create(name=name, musicbrainz_id=mbid)
        artist.fix_metadata()

    return artist


def get_or_create_album(
    name: str, artist: Artist, mbid: str = None
) -> Optional[Album]:
    album = None
    album_dict = lookup_album_dict_from_mb(name, artist_name=artist.name)

    name = name or album_dict.get("title", None)
    if not name:
        logger.debug(
            f"Cannot get or create album by {artist} with no name ({name})"
        )
        return

    album = Album.objects.filter(
        musicbrainz_id=mbid, name=name, artists__in=[artist]
    ).first()

    if not album:
        mbid_group = album_dict.get("mb_group_id")
        album = Album.objects.filter(
            musicbrainz_releasegroup_id=mbid_group
        ).first()

    if not album and name:
        mbid = mbid or album_dict["mb_id"]
        album, album_created = Album.objects.get_or_create(musicbrainz_id=mbid)
        if album_created:
            album.name = name
            album.year = album_dict["year"]
            album.musicbrainz_releasegroup_id = album_dict["mb_group_id"]
            album.musicbrainz_albumartist_id = artist.musicbrainz_id
            album.save(
                update_fields=[
                    "name",
                    "musicbrainz_id",
                    "year",
                    "musicbrainz_releasegroup_id",
                    "musicbrainz_albumartist_id",
                ]
            )
            album.artists.add(artist)
            album.fix_album_artist()
            album.fetch_artwork()
            album.scrape_allmusic()

    if not album:
        logger.warn(f"No album found for {name} and {mbid}")

    album.fix_album_artist()
    return album


def get_or_create_track(post_data: dict, post_keys: dict) -> Track:
    track_run_time_seconds = post_data.get(post_keys.get("RUN_TIME"), 0)
    if post_keys.get("RUN_TIME") == "RunTime":
        track_run_time_seconds = convert_to_seconds(
            post_data.get(post_keys.get("RUN_TIME"), 0)
        )

    artist_name = post_data.get(post_keys.get("ARTIST_NAME"), "")
    artist_mb_id = post_data.get(post_keys.get("ARTIST_MB_ID"), "")
    album_title = post_data.get(post_keys.get("ALBUM_NAME"), "")
    album_mb_id = post_data.get(post_keys.get("ALBUM_MB_ID"), "")
    track_title = post_data.get(post_keys.get("TRACK_TITLE"), "")
    track_mb_id = post_data.get(post_keys.get("TRACK_MB_ID"), "")

    artist = get_or_create_artist(
        artist_name,
        mbid=artist_mb_id,
    )
    album = get_or_create_album(
        album_title,
        artist=artist,
        mbid=album_mb_id,
    )

    track = None
    if not track_mb_id and album:
        try:
            track_mb_id = lookup_track_from_mb(
                track_title,
                artist.musicbrainz_id,
                album.musicbrainz_id,
            ).get("id", 0)
        except TypeError:
            pass

    if track_mb_id:
        track = Track.objects.filter(musicbrainz_id=track_mb_id).first()

    if not track:
        track = Track.objects.create(
            title=track_title,
            artist=artist,
            album=album,
            musicbrainz_id=track_mb_id,
            run_time_seconds=track_run_time_seconds,
        )
    return track


def get_or_create_various_artists():
    artist = Artist.objects.filter(name="Various Artists").first()
    if not artist:
        artist = Artist.objects.create(**VARIOUS_ARTIST_DICT)
        logger.info("Created Various Artists placeholder")
    return artist
