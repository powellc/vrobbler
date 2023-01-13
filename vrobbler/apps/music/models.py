import logging
from typing import Dict, Optional
from uuid import uuid4

import musicbrainzngs
from django.apps.config import cached_property
from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Artist(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    musicbrainz_id = models.CharField(max_length=255, **BNULL)

    class Meta:
        unique_together = [['name', 'musicbrainz_id']]

    def __str__(self):
        return self.name

    @property
    def mb_link(self):
        return f"https://musicbrainz.org/artist/{self.musicbrainz_id}"


class Album(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    artists = models.ManyToManyField(Artist)
    year = models.IntegerField(**BNULL)
    musicbrainz_id = models.CharField(max_length=255, unique=True, **BNULL)
    musicbrainz_releasegroup_id = models.CharField(max_length=255, **BNULL)
    musicbrainz_albumartist_id = models.CharField(max_length=255, **BNULL)
    cover_image = models.ImageField(upload_to="albums/", **BNULL)

    def __str__(self):
        return self.name

    @property
    def primary_artist(self):
        return self.artists.first()

    def fix_metadata(self):
        if not self.musicbrainz_albumartist_id or not self.year:
            musicbrainzngs.set_useragent('vrobbler', '0.3.0')
            mb_data = musicbrainzngs.get_release_by_id(
                self.musicbrainz_id, includes=['artists']
            )
            if not self.musicbrainz_albumartist_id:
                self.musicbrainz_albumartist_id = mb_data['release'][
                    'artist-credit'
                ][0]['artist']['id']
            if not self.year:
                try:
                    self.year = mb_data['release']['date'][0:4]
                except KeyError:
                    pass
                except IndexError:
                    pass

            self.save(update_fields=['musicbrainz_albumartist_id', 'year'])

            new_artist = Artist.objects.filter(
                musicbrainz_id=self.musicbrainz_albumartist_id
            ).first()
            if self.musicbrainz_albumartist_id and new_artist:
                self.artists.add(new_artist)
            if not new_artist:
                for t in self.track_set.all():
                    self.artists.add(t.artist)

    def fetch_artwork(self):
        if not self.cover_image:
            try:
                img_data = musicbrainzngs.get_image_front(self.musicbrainz_id)
                name = f"{self.name}_{self.uuid}.jpg"
                self.cover_image = ContentFile(img_data, name=name)
            except musicbrainzngs.ResponseError:
                logger.warning(f'No cover art found for {self.name}')
                self.cover_image = 'default-image-replace-me'
            self.save()

    @property
    def mb_link(self):
        return f"https://musicbrainz.org/release/{self.musicbrainz_id}"


class Track(ScrobblableMixin):
    class Opinion(models.IntegerChoices):
        DOWN = -1, 'Thumbs down'
        NEUTRAL = 0, 'No opinion'
        UP = 1, 'Thumbs up'

    artist = models.ForeignKey(Artist, on_delete=models.DO_NOTHING)
    album = models.ForeignKey(Album, on_delete=models.DO_NOTHING, **BNULL)
    musicbrainz_id = models.CharField(max_length=255, unique=True, **BNULL)

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
                f"No artist or artist musicbrainz ID found in message from source, not scrobbling"
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

        album.fix_metadata()
        if not album.cover_image:
            album.fetch_artwork()

        track_dict['album_id'] = getattr(album, "id", None)
        track_dict['artist_id'] = artist.id

        track, created = cls.objects.get_or_create(**track_dict)
        if created:
            logger.debug(f"Created new track: {track}")
        else:
            logger.debug(f"Found track {track}")

        return track
