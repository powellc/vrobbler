import logging
from typing import Dict
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class VideoGameCollection(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    cover = models.ImageField(upload_to="games/series-covers/", **BNULL)
    igdb_id = models.IntegerField(**BNULL)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "videogames:videogamecollection_detail", kwargs={"slug": self.uuid}
        )


class VideoGame(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "GAME_COMPLETION_PERCENT", 100)

    title = models.CharField(max_length=255)
    igdb_id = models.IntegerField(**BNULL)
    alternative_name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    cover = models.ImageField(upload_to="games/covers/", **BNULL)
    screenshot = models.ImageField(upload_to="games/covers/", **BNULL)
    rating = models.FloatField(**BNULL)
    rating_count = models.IntegerField(**BNULL)
    release_date = models.DateTimeField(**BNULL)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "videogames:videogame_detail", kwargs={"slug": self.uuid}
        )

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> "VideoGame":
        ...
