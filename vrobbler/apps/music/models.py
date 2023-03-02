import logging
from tempfile import NamedTemporaryFile
from typing import Dict, Optional
from urllib.request import urlopen
from uuid import uuid4

import musicbrainzngs
from django.conf import settings
from django.core.files.base import ContentFile, File
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin
from scrobbles.theaudiodb import lookup_artist_from_tadb
from vrobbler.apps.scrobbles.theaudiodb import lookup_album_from_tadb

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Artist(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    biography = models.TextField(**BNULL)
    theaudiodb_genre = models.CharField(max_length=255, **BNULL)
    theaudiodb_mood = models.CharField(max_length=255, **BNULL)
    musicbrainz_id = models.CharField(max_length=255, **BNULL)
    thumbnail = models.ImageField(upload_to="artist/", **BNULL)

    class Meta:
        unique_together = [['name', 'musicbrainz_id']]

    def __str__(self):
        return self.name

    @property
    def mb_link(self):
        return f"https://musicbrainz.org/artist/{self.musicbrainz_id}"

    def get_absolute_url(self):
        return reverse('music:artist_detail', kwargs={'slug': self.uuid})

    def scrobbles(self):
        from scrobbles.models import Scrobble

        return Scrobble.objects.filter(
            track__in=self.track_set.all()
        ).order_by('-timestamp')

    @property
    def tracks(self):
        return (
            self.track_set.all()
            .annotate(scrobble_count=models.Count('scrobble'))
            .order_by('-scrobble_count')
        )

    def charts(self):
        from scrobbles.models import ChartRecord

        return ChartRecord.objects.filter(track__artist=self).order_by('-year')

    def fix_metadata(self):
        tadb_info = lookup_artist_from_tadb(self.name)
        if not tadb_info:
            logger.warn(f"No response from TADB for artist {self.name}")
            return

        self.biography = tadb_info['biography']
        self.theaudiodb_genre = tadb_info['genre']
        self.theaudiodb_mood = tadb_info['mood']

        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(urlopen(tadb_info['thumb_url']).read())
        img_temp.flush()
        img_filename = f"{self.name}_{self.uuid}.jpg"
        self.thumbnail.save(img_filename, File(img_temp))


class Album(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    artists = models.ManyToManyField(Artist)
    year = models.IntegerField(**BNULL)
    musicbrainz_id = models.CharField(max_length=255, unique=True, **BNULL)
    musicbrainz_releasegroup_id = models.CharField(max_length=255, **BNULL)
    musicbrainz_albumartist_id = models.CharField(max_length=255, **BNULL)
    cover_image = models.ImageField(upload_to="albums/", **BNULL)
    theaudiodb_id = models.CharField(max_length=255, unique=True, **BNULL)
    theaudiodb_description = models.TextField(**BNULL)
    theaudiodb_year_released = models.IntegerField(**BNULL)
    theaudiodb_score = models.FloatField(**BNULL)
    theaudiodb_score_votes = models.IntegerField(**BNULL)
    theaudiodb_genre = models.CharField(max_length=255, **BNULL)
    theaudiodb_style = models.CharField(max_length=255, **BNULL)
    theaudiodb_mood = models.CharField(max_length=255, **BNULL)
    theaudiodb_speed = models.CharField(max_length=255, **BNULL)
    theaudiodb_theme = models.CharField(max_length=255, **BNULL)
    allmusic_id = models.CharField(max_length=255, **BNULL)
    rateyourmusic_id = models.CharField(max_length=255, **BNULL)
    wikipedia_slug = models.CharField(max_length=255, **BNULL)
    discogs_id = models.CharField(max_length=255, **BNULL)
    wikidata_id = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("music:album_detail", kwargs={'slug': self.uuid})

    def scrobbles(self):
        from scrobbles.models import Scrobble

        return Scrobble.objects.filter(
            track__in=self.track_set.all()
        ).order_by('-timestamp')

    @property
    def tracks(self):
        return (
            self.track_set.all()
            .annotate(scrobble_count=models.Count('scrobble'))
            .order_by('-scrobble_count')
        )

    @property
    def primary_artist(self):
        return self.artists.first()

    def scrape_theaudiodb(self) -> None:
        artist = "Various Artists"
        if self.primary_artist:
            artist = self.primary_artist.name
        album_data = lookup_album_from_tadb(self.name, artist)
        if not album_data.get('theaudiodb_id'):
            logger.info(f"No data for {self} found in TheAudioDB")
            return

        Album.objects.filter(pk=self.pk).update(**album_data)

    def fix_metadata(self):
        if (
            not self.musicbrainz_albumartist_id
            or not self.year
            or not self.musicbrainz_releasegroup_id
        ):
            musicbrainzngs.set_useragent('vrobbler', '0.3.0')
            mb_data = musicbrainzngs.get_release_by_id(
                self.musicbrainz_id, includes=['artists', 'release-groups']
            )
            if not self.musicbrainz_releasegroup_id:
                self.musicbrainz_releasegroup_id = mb_data['release'][
                    'release-group'
                ]['id']
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

            self.save(
                update_fields=[
                    'musicbrainz_albumartist_id',
                    'musicbrainz_releasegroup_id',
                    'year',
                ]
            )

            new_artist = Artist.objects.filter(
                musicbrainz_id=self.musicbrainz_albumartist_id
            ).first()
            if self.musicbrainz_albumartist_id and new_artist:
                self.artists.add(new_artist)
            if not new_artist:
                for t in self.track_set.all():
                    self.artists.add(t.artist)
            if (
                not self.cover_image
                or self.cover_image == 'default-image-replace-me'
            ):
                self.fetch_artwork()
        self.scrape_theaudiodb()

    def fetch_artwork(self, force=False):
        if not self.cover_image and not force:
            if self.musicbrainz_id:
                try:
                    img_data = musicbrainzngs.get_image_front(
                        self.musicbrainz_id
                    )
                    name = f"{self.name}_{self.uuid}.jpg"
                    self.cover_image = ContentFile(img_data, name=name)
                    logger.info(f'Setting image to {name}')
                except musicbrainzngs.ResponseError:
                    logger.warning(
                        f'No cover art found for {self.name} by release'
                    )

            if (
                not self.cover_image
                or self.cover_image == "default-image-replace-me"
            ) and self.musicbrainz_releasegroup_id:
                try:
                    img_data = musicbrainzngs.get_release_group_image_front(
                        self.musicbrainz_releasegroup_id
                    )
                    name = f"{self.name}_{self.uuid}.jpg"
                    self.cover_image = ContentFile(img_data, name=name)
                    logger.info(f'Setting image to {name}')
                except musicbrainzngs.ResponseError:
                    logger.warning(
                        f'No cover art found for {self.name} by release group'
                    )
            if not self.cover_image:
                logger.debug(
                    f"No cover art found for release or release group for {self.name}, setting to default"
                )
            self.save()

    @property
    def mb_link(self) -> str:
        return f"https://musicbrainz.org/release/{self.musicbrainz_id}"

    @property
    def allmusic_link(self) -> str:
        if self.allmusic_id:
            return f"https://www.allmusic.com/artist/{self.allmusic_id}"
        return ""

    @property
    def wikipedia_link(self):
        if self.wikipedia_slug:
            return f"https://www.wikipedia.org/en/{self.wikipedia_slug}"
        return ""

    @property
    def tadb_link(self):
        if self.theaudiodb_id:
            return f"https://www.theaudiodb.com/album/{self.theaudiodb_id}"
        return ""


class Track(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, 'MUSIC_COMPLETION_PERCENT', 90)

    class Opinion(models.IntegerChoices):
        DOWN = -1, 'Thumbs down'
        NEUTRAL = 0, 'No opinion'
        UP = 1, 'Thumbs up'

    artist = models.ForeignKey(Artist, on_delete=models.DO_NOTHING)
    album = models.ForeignKey(Album, on_delete=models.DO_NOTHING, **BNULL)
    musicbrainz_id = models.CharField(max_length=255, **BNULL)

    class Meta:
        unique_together = [['album', 'musicbrainz_id']]

    def __str__(self):
        return f"{self.title} by {self.artist}"

    def get_absolute_url(self):
        return reverse('music:track_detail', kwargs={'slug': self.uuid})

    @property
    def subtitle(self):
        return self.artist

    @property
    def mb_link(self):
        return f"https://musicbrainz.org/recording/{self.musicbrainz_id}"

    @property
    def info_link(self):
        return self.mb_link

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
        album, album_created = Album.objects.get_or_create(**album_dict)

        album.fix_metadata()
        if not album.cover_image:
            album.fetch_artwork()

        track_dict['album_id'] = getattr(album, "id", None)
        track_dict['artist_id'] = artist.id

        track, created = cls.objects.get_or_create(**track_dict)

        return track
