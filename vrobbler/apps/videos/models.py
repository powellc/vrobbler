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
from scrobbles.mixins import ObjectWithGenres, ScrobblableMixin
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

    genre = TaggableManager(through=ObjectWithGenres)

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("videos:series_detail", kwargs={"slug": self.uuid})

    def imdb_link(self):
        return f"https://www.imdb.com/title/tt{self.imdb_id}"

    def scrobbles_for_user(self, user_id: int):
        from scrobbles.models import Scrobble

        return Scrobble.objects.filter(
            video__tv_series=self, user=user_id, played_to_completion=True
        ).order_by("-timestamp")

    def fix_metadata(self, force_update=False):
        name_or_id = self.name
        if self.imdb_id:
            name_or_id = self.imdb_id
        imdb_dict = lookup_video_from_imdb(name_or_id)
        if not imdb_dict:
            logger.warn(f"No imdb data for {self}")
            return

        self.imdb_id = imdb_dict.data.get("imdbID")
        self.imdb_rating = imdb_dict.data.get("arithmetic mean")
        self.plot = imdb_dict.data.get("plot outline")
        self.save(update_fields=["imdb_id", "imdb_rating", "plot"])

        cover_url = imdb_dict.get("cover url")

        if (not self.cover_image or force_update) and cover_url:
            r = requests.get(cover_url)
            if r.status_code == 200:
                fname = f"{self.name}_{self.uuid}.jpg"
                self.cover_image.save(fname, ContentFile(r.content), save=True)

        if genres := imdb_dict.data.get("genres"):
            self.genre.add(*genres)


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
        return f"https://www.imdb.com/title/tt{self.imdb_id}"

    @property
    def info_link(self):
        return self.imdb_link

    @property
    def link(self):
        return self.imdb_link

    def fix_metadata(self, force_update=False):
        imdb_dict = lookup_video_from_imdb(self.imdb_id)
        if not imdb_dict:
            logger.warn(f"No imdb data for {self}")
            return
        if imdb_dict.get("runtimes") and len(imdb_dict.get("runtimes")) > 0:
            self.run_time_seconds = int(imdb_dict.get("runtimes")[0]) * 60
        self.imdb_rating = imdb_dict.data.get("rating")
        self.plot = imdb_dict.data.get("plot")
        self.year = imdb_dict.data.get("year")
        self.save(
            update_fields=["imdb_rating", "plot", "year", "run_time_seconds"]
        )

        cover_url = imdb_dict.get("cover url")

        if (not self.cover_image or force_update) and cover_url:
            r = requests.get(cover_url)
            if r.status_code == 200:
                fname = f"{self.title}_{self.uuid}.jpg"
                self.cover_image.save(fname, ContentFile(r.content), save=True)

        if genres := imdb_dict.data.get("genres"):
            self.genre.add(*genres)

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
