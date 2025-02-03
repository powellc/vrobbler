import logging
from typing import Optional
from uuid import uuid4

import pendulum
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from music.constants import JELLYFIN_POST_KEYS
from scrobbles.mixins import (
    ObjectWithGenres,
    ScrobblableConstants,
    ScrobblableMixin,
)
from taggit.managers import TaggableManager
from videos.metadata import VideoMetadata
from videos.sources.imdb import lookup_video_from_imdb

from vrobbler.apps.videos.sources.youtube import lookup_video_from_youtube

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/channel/"
IMDB_VIDEO_URL = "https://www.imdb.com/title/tt"

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Channel(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    cover_image = models.ImageField(upload_to="videos/channels/", **BNULL)
    cover_small = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    cover_medium = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    youtube_id = models.CharField(max_length=255, **BNULL)
    genre = TaggableManager(through=ObjectWithGenres)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("videos:channel_detail", kwargs={"slug": self.uuid})

    @property
    def youtube_url(self):
        return YOUTUBE_CHANNEL_URL + self.youtube_id

    @property
    def primary_image_url(self) -> str:
        url = ""
        if self.cover_image:
            url = self.cover_image_medium.url
        return url

    def scrobbles_for_user(self, user_id: int, include_playing=False):
        from scrobbles.models import Scrobble

        played_query = models.Q(played_to_completion=True)
        if include_playing:
            played_query = models.Q()
        return Scrobble.objects.filter(
            played_query,
            video__channel=self,
            user=user_id,
        ).order_by("-timestamp")

    def fix_metadata(self, force: bool = False):
        # TODO Scrape channel info from Youtube
        logger.warning("Not implemented yet")
        return


class Series(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    plot = models.TextField(**BNULL)
    imdb_id = models.CharField(max_length=20, **BNULL)
    imdb_rating = models.FloatField(**BNULL)
    cover_image = models.ImageField(upload_to="videos/series/", **BNULL)
    cover_small = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    cover_medium = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    preferred_source = models.CharField(max_length=100, **BNULL)

    genre = TaggableManager(through=ObjectWithGenres)

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("videos:series_detail", kwargs={"slug": self.uuid})

    def imdb_link(self) -> str:
        if self.imdb_id:
            return IMDB_VIDEO_URL + self.imdb_id
        return ""

    @property
    def primary_image_url(self) -> str:
        url = ""
        if self.cover_image:
            url = self.cover_image_medium.url
        return url

    def scrobbles_for_user(self, user_id: int, include_playing=False):
        from scrobbles.models import Scrobble

        played_query = models.Q(played_to_completion=True)
        if include_playing:
            played_query = models.Q()
        return Scrobble.objects.filter(
            played_query,
            video__tv_series=self,
            user=user_id,
        ).order_by("-timestamp")

    def last_scrobbled_episode(self, user_id: int) -> Optional["Video"]:
        episode = None
        last_scrobble = self.scrobbles_for_user(
            user_id, include_playing=True
        ).first()
        if last_scrobble:
            episode = last_scrobble.media_obj
        return episode

    def is_episode_playing(self, user_id: int) -> bool:
        last_scrobble = self.scrobbles_for_user(
            user_id, include_playing=True
        ).first()
        return not last_scrobble.played_to_completion

    def fix_metadata(self, force_update=False):
        name_or_id = self.name
        if self.imdb_id:
            name_or_id = self.imdb_id
        video_metadata: VideoMetadata = lookup_video_from_imdb(name_or_id)

        if not video_metadata.title:
            logger.warning(f"No imdb data for {self}")
            return

        cover_url = imdb_dict.get("cover_url")

        if (not self.cover_image or force_update) and cover_url:
            r = requests.get(cover_url)
            if r.status_code == 200:
                fname = f"{self.name}_{self.uuid}.jpg"
                self.cover_image.save(fname, ContentFile(r.content), save=True)

        if genres := imdb_dict.get("genres"):
            self.genre.add(*genres)


class Video(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "VIDEO_COMPLETION_PERCENT", 90)
    SECONDS_TO_STALE = getattr(settings, "VIDEO_SECONDS_TO_STALE", 14400)
    METADATA_CLASS = VideoMetadata

    class VideoType(models.TextChoices):
        UNKNOWN = "U", _("Unknown")
        TV_EPISODE = "E", _("TV Episode")
        MOVIE = "M", _("Movie")
        SKATE_VIDEO = "S", _("Skate Video")
        YOUTUBE = "Y", _("YouTube Video")

    video_type = models.CharField(
        max_length=1,
        choices=VideoType.choices,
        default=VideoType.UNKNOWN,
    )
    overview = models.TextField(**BNULL)
    tagline = models.TextField(**BNULL)
    year = models.IntegerField(**BNULL)

    # TV show specific fields
    tv_series = models.ForeignKey(Series, on_delete=models.DO_NOTHING, **BNULL)
    channel = models.ForeignKey(Channel, on_delete=models.DO_NOTHING, **BNULL)
    season_number = models.IntegerField(**BNULL)
    episode_number = models.IntegerField(**BNULL)
    next_imdb_id = models.CharField(max_length=20, **BNULL)
    imdb_id = models.CharField(max_length=20, **BNULL)
    imdb_rating = models.FloatField(**BNULL)
    cover_image = models.ImageField(upload_to="videos/video/", **BNULL)
    cover_image_small = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    cover_image_medium = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    tvrage_id = models.CharField(max_length=20, **BNULL)
    tvdb_id = models.CharField(max_length=20, **BNULL)
    tmdb_id = models.CharField(max_length=20, **BNULL)
    youtube_id = models.CharField(max_length=255, **BNULL)
    plot = models.TextField(**BNULL)
    upload_date = models.DateField(**BNULL)

    class Meta:
        unique_together = [["title", "imdb_id"]]

    def __str__(self):
        if not self.title:
            return self.youtube_id or self.imdb_id
        if self.video_type == self.VideoType.TV_EPISODE:
            return f"{self.title} / [S{self.season_number}E{self.episode_number}] {self.tv_series}"
        if self.video_type == self.VideoType.YOUTUBE:
            return f"{self.title} / {self.channel}"
        return self.title

    def get_absolute_url(self):
        return reverse("videos:video_detail", kwargs={"slug": self.uuid})

    @property
    def subtitle(self):
        if self.tv_series:
            return self.tv_series
        return ""

    @property
    def imdb_link(self):
        return f"https://www.imdb.com/title/tt{self.imdb_id}"

    @property
    def info_link(self):
        return self.imdb_link

    @property
    def link(self) -> str:
        return self.imdb_link

    @property
    def youtube_link(self) -> str:
        if self.youtube_id:
            return f"https://www.youtube.com/watch?v={self.youtube_id}"
        return ""

    @property
    def primary_image_url(self) -> str:
        url = ""
        if self.cover_image:
            url = self.cover_image_medium.url
        return url

    @property
    def strings(self) -> ScrobblableConstants:
        return ScrobblableConstants(verb="Watching", tags="movie_camera")

    def save_image_from_url(self, url: str, force_update: bool = False):
        if not self.cover_image or (force_update and url):
            r = requests.get(url)
            if r.status_code == 200:
                fname = f"{self.title}_{self.uuid}.jpg"
                self.cover_image.save(fname, ContentFile(r.content), save=True)

    @classmethod
    def get_from_youtube_id(
        cls, youtube_id: str, overwrite: bool = False
    ) -> "Video":
        video, created = cls.objects.get_or_create(youtube_id=youtube_id)
        if not created and not overwrite:
            return video

        vdict, cover, genres = lookup_video_from_youtube(
            youtube_id
        ).as_dict_with_cover_and_genres()
        if created or overwrite:
            for k, v in vdict.items():
                setattr(video, k, v)
            video.save()

            video.save_image_from_url(cover)
            video.genre.add(*genres)
        return video

    @classmethod
    def get_from_imdb_id(cls, imdb_id: str, overwrite: bool = False):
        video, created = cls.objects.get_or_create(imdb_id=imdb_id)
        if not created and not overwrite:
            return video

        vdict, cover, genres = lookup_video_from_imdb(
            imdb_id
        ).as_dict_with_cover_and_genres()
        if created or overwrite:
            for k, v in vdict.items():
                setattr(video, k, v)
            video.save()

            video.save_image_from_url(cover)
            video.genre.add(*genres)
        return video

    @classmethod
    def find_or_create(
        cls, data_dict: dict, post_keys: dict = JELLYFIN_POST_KEYS
    ) -> Optional["Video"]:
        """Thes smallest of wrappers around our actual get or create utility."""
        imdb_key = post_keys.get("IMDB_ID", "").replace("tt", "")
        return cls.get_from_imdb_id(data_dict.get(imdb_key))
