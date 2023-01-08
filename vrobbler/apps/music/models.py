import logging
from typing import Dict, Optional
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from vrobbler.apps.music.constants import JELLYFIN_POST_KEYS as KEYS

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Album(TimeStampedModel):
    name = models.CharField(max_length=255)
    year = models.IntegerField()
    musicbrainz_id = models.CharField(max_length=255, **BNULL)
    musicbrainz_releasegroup_id = models.CharField(max_length=255, **BNULL)
    musicbrainz_albumartist_id = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return self.name


class Artist(TimeStampedModel):
    name = models.CharField(max_length=255)
    musicbrainz_id = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return self.name


class Track(TimeStampedModel):
    title = models.CharField(max_length=255, **BNULL)
    artist = models.ForeignKey(Artist, on_delete=models.DO_NOTHING)
    album = models.ForeignKey(Album, on_delete=models.DO_NOTHING, **BNULL)
    musicbrainz_id = models.CharField(max_length=255, **BNULL)
    run_time = models.CharField(max_length=8, **BNULL)
    run_time_ticks = models.PositiveBigIntegerField(**BNULL)

    def __str__(self):
        return f"{self.title} by {self.artist}"

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> Optional["Track"]:
        """Given a data dict from Jellyfin, does the heavy lifting of looking up
        the video and, if need, TV Series, creating both if they don't yet
        exist.

        """
        artist = data_dict.get(KEYS["ARTIST_NAME"], None)
        artist_musicbrainz_id = data_dict.get(KEYS["ARTIST_MB_ID"], None)
        if not artist or not artist_musicbrainz_id:
            logger.warning(
                f"No artist or artist musicbrainz ID found in message from Jellyfin, not scrobbling"
            )
            return
        artist, artist_created = Artist.objects.get_or_create(
            name=artist, musicbrainz_id=artist_musicbrainz_id
        )
        if artist_created:
            logger.debug(f"Created new album {artist}")
        else:
            logger.debug(f"Found album {artist}")

        album = None
        album_name = data_dict.get(KEYS["ALBUM_NAME"], None)
        if album_name:
            album_dict = {
                "name": album_name,
                "year": data_dict.get(KEYS["YEAR"], ""),
                "musicbrainz_id": data_dict.get(KEYS['ALBUM_MB_ID']),
                "musicbrainz_releasegroup_id": data_dict.get(
                    KEYS["RELEASEGROUP_MB_ID"]
                ),
                "musicbrainz_albumartist_id": data_dict.get(
                    KEYS["ARTIST_MB_ID"]
                ),
            }
            album, album_created = Album.objects.get_or_create(**album_dict)
            if album_created:
                logger.debug(f"Created new album {album}")
            else:
                logger.debug(f"Found album {album}")

        track_dict = {
            "title": data_dict.get("Name", ""),
            "musicbrainz_id": data_dict.get(KEYS["TRACK_MB_ID"], None),
            "run_time_ticks": data_dict.get(KEYS["RUN_TIME_TICKS"], None),
            "run_time": data_dict.get(KEYS["RUN_TIME"], None),
            "album_id": getattr(album, "id", None),
            "artist_id": artist.id,
        }

        track, created = cls.objects.get_or_create(**track_dict)
        if created:
            logger.debug(f"Created new track: {track}")
        else:
            logger.debug(f"Found track{track}")

        return track
