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
    year = models.IntegerField(**BNULL)
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
    def find_or_create(
        cls, artist_dict: Dict, album_dict: Dict, track_dict: Dict
    ) -> Optional["Track"]:
        """Given a data dict from Jellyfin, does the heavy lifting of looking up
        the video and, if need, TV Series, creating both if they don't yet
        exist.

        """
        if not artist_dict.get('name') or not artist_dict.get(
            'musicbrainz_id'
        ):
            logger.warning(
                f"No artist or artist musicbrainz ID found in message from Jellyfin, not scrobbling"
            )
            return
        artist, artist_created = Artist.objects.get_or_create(**artist_dict)
        if artist_created:
            logger.debug(f"Created new album {artist}")
        else:
            logger.debug(f"Found album {artist}")

        album, album_created = Album.objects.get_or_create(**album_dict)
        if album_created:
            logger.debug(f"Created new album {album}")
        else:
            logger.debug(f"Found album {album}")

        track_dict['album_id'] = getattr(album, "id", None)
        track_dict['artist_id'] = artist.id

        track, created = cls.objects.get_or_create(**track_dict)
        if created:
            logger.debug(f"Created new track: {track}")
        else:
            logger.debug(f"Found track{track}")

        return track
