import logging
import re

from musicbrainzngs.caa import musicbrainz

from scrobbles.musicbrainz import (
    lookup_album_dict_from_mb,
    lookup_artist_from_mb,
    lookup_track_from_mb,
)

logger = logging.getLogger(__name__)


from music.models import Album, Artist, Track


def get_or_create_artist(name: str, mbid: str = None) -> Artist:
    artist = None
    logger.debug(f'Got artist {name} and mbid: {mbid}')

    if 'feat.' in name.lower():
        name = re.split("feat.", name, flags=re.IGNORECASE)[0].strip()
    if 'featuring' in name.lower():
        name = re.split("featuring", name, flags=re.IGNORECASE)[0].strip()
    if '&' in name.lower():
        name = re.split("&", name, flags=re.IGNORECASE)[0].strip()

    artist_dict = lookup_artist_from_mb(name)
    mbid = mbid or artist_dict['id']

    logger.debug(f'Looking up artist {name} and mbid: {mbid}')
    artist = Artist.objects.filter(musicbrainz_id=mbid).first()
    if not artist:
        artist = Artist.objects.create(name=name, musicbrainz_id=mbid)
        logger.debug(
            f"Created artist {artist.name} ({artist.musicbrainz_id}) "
        )
        artist.fix_metadata()

    return artist


def get_or_create_album(name: str, artist: Artist, mbid: str = None) -> Album:
    album = None
    album_created = False
    albums = Album.objects.filter(name__iexact=name)
    if albums.count() == 1:
        album = albums.first()
    else:
        for potential_album in albums:
            if artist in album.artist_set.all():
                album = potential_album
    if not album:
        album_created = True
        album = Album.objects.create(name=name, musicbrainz_id=mbid)
        album.save()
        album.artists.add(artist)

    if album_created or not mbid:
        album_dict = lookup_album_dict_from_mb(
            album.name, artist_name=artist.name
        )
        album.year = album_dict["year"]
        album.musicbrainz_id = album_dict["mb_id"]
        album.musicbrainz_releasegroup_id = album_dict["mb_group_id"]
        album.musicbrainz_albumartist_id = artist.musicbrainz_id
        album.save(
            update_fields=[
                "year",
                "musicbrainz_id",
                "musicbrainz_releasegroup_id",
                "musicbrainz_albumartist_id",
            ]
        )
        album.artists.add(artist)
        album.fetch_artwork()
    return album


def get_or_create_track(
    title: str,
    artist: Artist,
    album: Album,
    mbid: str = None,
    run_time=None,
    run_time_ticks=None,
) -> Track:
    track = None
    if not mbid:
        mbid = lookup_track_from_mb(
            title,
            artist.musicbrainz_id,
            album.musicbrainz_id,
        )['id']

    track = Track.objects.filter(musicbrainz_id=mbid).first()

    if not track:
        track = Track.objects.create(
            title=title,
            artist=artist,
            album=album,
            musicbrainz_id=mbid,
            run_time=run_time,
            run_time_ticks=run_time_ticks,
        )

    return track
