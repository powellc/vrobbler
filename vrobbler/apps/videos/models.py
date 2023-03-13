import logging
from typing import Dict
from uuid import uuid4

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin
from scrobbles.utils import convert_to_seconds
from taggit.managers import TaggableManager

from videos.imdb import lookup_video_from_imdb

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Series(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    plot = models.TextField(**BNULL)
    imdb_id = models.CharField(max_length=20, **BNULL)
    imdb_rating = models.FloatField(**BNULL)
    cover_image = models.ImageField(upload_to="videos/series/", **BNULL)

    genres = TaggableManager()

    def __str__(self):
        return self.name

    def imdb_link(self):
        return f"https://www.imdb.com/title/{self.imdb_id}"

    class Meta:
        verbose_name_plural = "series"

    def fix_metadata(self, force_update=False):
        imdb_dict = lookup_video_from_imdb(self.name, kind="tv series")
        logger.info(imdb_dict)
        self.imdb_id = imdb_dict.get("movieID")
        self.imdb_rating = imdb_dict.get("rating")
        self.plot = imdb_dict.get("plot outline")
        self.save(update_fields=["imdb_id", "imdb_rating", "plot"])

        cover_url = imdb_dict.get("cover url")

        if (not self.cover_image or force_update) and cover_url:
            r = requests.get(cover_url)
            if r.status_code == 200:
                fname = f"{self.name}_{self.uuid}.jpg"
                self.cover_image.save(fname, ContentFile(r.content), save=True)


class Video(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "VIDEO_COMPLETION_PERCENT", 90)
    SECONDS_TO_STALE = getattr(settings, "VIDEO_SECONDS_TO_STALE", 14400)

    class VideoType(models.TextChoices):
        UNKNOWN = "U", _("Unknown")
        TV_EPISODE = "E", _("TV Episode")
        MOVIE = "M", _("Movie")

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
    season_number = models.IntegerField(**BNULL)
    episode_number = models.IntegerField(**BNULL)
    imdb_id = models.CharField(max_length=20, **BNULL)
    imdb_rating = models.FloatField(**BNULL)
    cover_image = models.ImageField(upload_to="videos/video/", **BNULL)
    tvrage_id = models.CharField(max_length=20, **BNULL)
    tvdb_id = models.CharField(max_length=20, **BNULL)
    plot = models.TextField(**BNULL)
    year = models.IntegerField(**BNULL)

    class Meta:
        unique_together = [["title", "imdb_id"]]

    def __str__(self):
        if self.video_type == self.VideoType.TV_EPISODE:
            return f"{self.tv_series} - Season {self.season_number}, Episode {self.episode_number}"
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
        return f"https://www.imdb.com/title/{self.imdb_id}"

    @property
    def info_link(self):
        return self.imdb_link

    @property
    def link(self):
        return self.imdb_link

    def fix_metadata(self, force_update=False):
        imdb_dict = lookup_video_from_imdb(self.imdb_id)
        self.imdb_rating = imdb_dict.get("rating")
        self.plot = imdb_dict.get("plot outline")
        self.year = imdb_dict.get("year")
        self.save(update_fields=["imdb_rating", "plot", "year"])

        cover_url = imdb_dict.get("cover url")

        if (not self.cover_image or force_update) and cover_url:
            r = requests.get(cover_url)
            if r.status_code == 200:
                fname = f"{self.title}_{self.uuid}.jpg"
                self.cover_image.save(fname, ContentFile(r.content), save=True)

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> "Video":
        """Given a data dict from Jellyfin, does the heavy lifting of looking up
        the video and, if need, TV Series, creating both if they don't yet
        exist.

        """
        from videos.utils import (
            get_or_create_video,
            get_or_create_video_from_jellyfin,
        )

        if "NotificationType" not in data_dict.keys():
            name_or_id = data_dict.get("imdb_id") or data_dict.get("title")
            video = get_or_create_video(name_or_id)
            return video

        if not data_dict.get("Provider_imdb"):
            title = data_dict.get("Name", "")
            logger.warn(
                f"No IMDB ID from Jellyfin, check metadata for {title}"
            )
            return

        return get_or_create_video_from_jellyfin(data_dict)
