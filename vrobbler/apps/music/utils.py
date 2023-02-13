#!/usr/bin/env python3
from typing import Optional
from scrobbles.musicbrainz import (
    lookup_album_dict_from_mb,
    lookup_artist_id_from_mb,
)


from music.models import Artist, Album, Track


def get_or_create_artist(name: str) -> Artist:
    artist, artist_created = Artist.objects.get_or_create(name=name)
    if artist_created:
        artist.musicbrainz_id = lookup_artist_id_from_mb(artist.name)
        artist.save(update_fields=["musicbrainz_id"])
    return artist


def get_or_create_album(name: str, artist: Artist) -> Album:
    album = None
    album_created = False
    albums = Album.objects.filter(name=name)
    if albums.count() == 1:
        album = albums.first()
    else:
        for potential_album in albums:
            if artist in album.artist_set.all():
                album = potential_album
    if not album:
        album_created = True
        album = Album.objects.create(name=name)
        album.save()
        album.artists.add(artist)

    if album_created:
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
    mbid: str,
    artist: Artist,
    album: Album,
    run_time=None,
    run_time_ticks=None,
) -> Track:
    track, track_created = Track.objects.get_or_create(
        title=title,
        artist=artist,
        musicbrainz_id=mbid,
    )

    if track_created:
        track.album = album
        track.run_time = run_time
        track.run_time_ticks = run_time_ticks
        track.save(update_fields=['album', 'run_time', 'run_time_ticks'])

    return track
