import logging
from typing import Optional
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin


logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class VideoGamePlatform(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    logo = models.ImageField(upload_to="games/platform-logos/", **BNULL)
    igdb_id = models.IntegerField(**BNULL)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "videogames:platform_detail", kwargs={"slug": self.uuid}
        )


class VideoGameCollection(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    cover = models.ImageField(upload_to="games/series-covers/", **BNULL)
    igdb_id = models.IntegerField(**BNULL)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "videogames:collection_detail", kwargs={"slug": self.uuid}
        )


class VideoGame(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "GAME_COMPLETION_PERCENT", 100)

    FIELDS_FROM_IGDB = [
        "igdb_id",
        "alternative_name",
        "rating",
        "rating_count",
        "release_date",
        "cover",
        "screenshot",
    ]
    FIELDS_FROM_HLTB = [
        "hltb_id",
        "release_year",
        "main_story_time",
        "main_extra_time",
        "completionist_time",
        "hltb_score",
    ]

    title = models.CharField(max_length=255)
    igdb_id = models.IntegerField(**BNULL)
    hltb_id = models.IntegerField(**BNULL)
    alternative_name = models.CharField(max_length=255, **BNULL)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    cover = models.ImageField(upload_to="games/covers/", **BNULL)
    screenshot = models.ImageField(upload_to="games/screenshots/", **BNULL)
    hltb_cover = models.ImageField(upload_to="games/hltb_covers/", **BNULL)
    rating = models.FloatField(**BNULL)
    rating_count = models.IntegerField(**BNULL)
    release_date = models.DateTimeField(**BNULL)
    release_year = models.IntegerField(**BNULL)
    main_story_time = models.IntegerField(**BNULL)
    main_extra_time = models.IntegerField(**BNULL)
    completionist_time = models.IntegerField(**BNULL)
    hltb_score = models.FloatField(**BNULL)
    platforms = models.ManyToManyField(VideoGamePlatform)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "videogames:videogame_detail", kwargs={"slug": self.uuid}
        )

    def hltb_link(self):
        return f"https://howlongtobeat.com/game/{self.hltb_id}"

    def fix_metadata(
        self,
        force_update: bool = False,
    ):
        from videogames.utils import (
            get_or_create_videogame,
            load_game_data_from_igdb,
        )

        if self.hltb_id and force_update:
            get_or_create_videogame(str(self.hltb_id), force_update)

        if self.igdb_id:
            load_game_data_from_igdb(self.id)
