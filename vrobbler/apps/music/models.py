import logging
from typing import Dict, Optional
from uuid import uuid4

from django.apps.config import cached_property

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Album(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    year = models.IntegerField(**BNULL)
    musicbrainz_id = models.CharField(max_length=255, unique=True, **BNULL)
    musicbrainz_releasegroup_id = models.CharField(max_length=255, **BNULL)
    musicbrainz_albumartist_id = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return self.name

    @property
    def mb_link(self):
        return f"https://musicbrainz.org/release/{self.musicbrainz_id}"


class Artist(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    musicbrainz_id = models.CharField(max_length=255, **BNULL)

    class Meta:
        unique_together=[['name', 'musicbrainz_id']]

    def __str__(self):
        return self.name

    @property
    def mb_link(self):
        return f"https://musicbrainz.org/artist/{self.musicbrainz_id}"


class Track(TimeStampedModel):
    class Opinion(models.IntegerChoices):
        DOWN = -1, 'Thumbs down'
        NEUTRAL = 0, 'No opinion'
        UP = 1, 'Thumbs up'

    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    title = models.CharField(max_length=255, **BNULL)
    artist = models.ForeignKey(Artist, on_delete=models.DO_NOTHING)
    album = models.ForeignKey(Album, on_delete=models.DO_NOTHING, **BNULL)
    musicbrainz_id = models.CharField(max_length=255, unique=True, **BNULL)
    run_time = models.CharField(max_length=8, **BNULL)
    run_time_ticks = models.PositiveBigIntegerField(**BNULL)
    # thumbs = models.IntegerField(default=Opinion.NEUTRAL, choices=Opinion.choices)

    def __str__(self):
        return f"{self.title} by {self.artist}"

    @property
    def mb_link(self):
        return f"https://musicbrainz.org/recording/{self.musicbrainz_id}"

    @cached_property
    def scrobble_count(self):
        return self.scrobble_set.filter(in_progress=False).count()

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
            logger.debug(f"Found track {track}")

        return track
