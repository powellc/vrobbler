import logging
import re
from typing import Optional

from music.musicbrainz import (
    lookup_album_dict_from_mb,
    lookup_artist_from_mb,
    lookup_track_from_mb,
)
from music.constants import VARIOUS_ARTIST_DICT

logger = logging.getLogger(__name__)


from music.models import Album, Artist, Track


def get_or_create_artist(name: str, mbid: str = None) -> Artist:
    artist = None
    logger.debug(f"Got artist {name} and mbid: {mbid}")

    if "feat." in name.lower():
        name = re.split("feat.", name, flags=re.IGNORECASE)[0].strip()
    if "featuring" in name.lower():
        name = re.split("featuring", name, flags=re.IGNORECASE)[0].strip()
    if "&" in name.lower():
        name = re.split("&", name, flags=re.IGNORECASE)[0].strip()

    artist_dict = lookup_artist_from_mb(name)
    mbid = mbid or artist_dict["id"]

    logger.debug(f"Looking up artist {name} and mbid: {mbid}")
    artist = Artist.objects.filter(musicbrainz_id=mbid).first()
    if not artist:
        artist = Artist.objects.create(name=name, musicbrainz_id=mbid)
        logger.debug(
            f"Created artist {artist.name} ({artist.musicbrainz_id}) "
        )
        artist.fix_metadata()

    return artist


def get_or_create_album(
    name: str, artist: Artist, mbid: str = None
) -> Optional[Album]:
    album = None
    album_dict = lookup_album_dict_from_mb(name, artist_name=artist.name)

    name = name or album_dict["title"]

    logger.debug(f"Looking up album {name} and mbid: {mbid}")

    album = Album.objects.filter(artists__in=[artist], name=name).first()

    if not album and name:
        mbid = mbid or album_dict["mb_id"]
        album, album_created = Album.objects.get_or_create(
            name=name, musicbrainz_id=mbid
        )
        if album_created:
            album.year = album_dict["year"]
            album.musicbrainz_releasegroup_id = album_dict["mb_group_id"]
            album.musicbrainz_albumartist_id = artist.musicbrainz_id
            album.save(
                update_fields=[
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


def get_or_create_track(
    title: str,
    artist: Artist,
    album: Album,
    mbid: str = None,
    run_time_seconds=None,
) -> Track:
    track = None
    if not mbid:
        mbid = lookup_track_from_mb(
            title,
            artist.musicbrainz_id,
            album.musicbrainz_id,
        )["id"]

    track = Track.objects.filter(musicbrainz_id=mbid).first()

    if not track:
        track = Track.objects.create(
            title=title,
            artist=artist,
            album=album,
            musicbrainz_id=mbid,
            run_time_seconds=run_time_seconds,
        )

    return track


def get_or_create_various_artists():
    artist = Artist.objects.filter(name="Various Artists").first()
    if not artist:
        artist = Artist.objects.create(**VARIOUS_ARTIST_DICT)
        logger.info("Created Various Artists placeholder")
    return artist
