import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from scrobbles.mixins import ScrobblableConstants, ScrobblableMixin

from vrobbler.apps.scrobbles.dataclasses import MoodLogData

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}
User = get_user_model()


class Mood(ScrobblableMixin):
    description = models.TextField(**BNULL)
    image = models.ImageField(upload_to="moods/", **BNULL)
    image_small = ImageSpecField(
        source="thumbnail",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    image_medium = ImageSpecField(
        source="thumbnail",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )

    def __str__(self):
        if self.title:
            return self.title
        return str(self.uuid)

    def get_absolute_url(self):
        return reverse("moods:mood-detail", kwargs={"slug": self.uuid})

    def get_start_url(self):
        return reverse("scrobbles:start", kwargs={"uuid": self.uuid})

    @property
    def subtitle(self) -> str:
        return ""

    @property
    def strings(self) -> ScrobblableConstants:
        return ScrobblableConstants(verb="Feeling", tags="thinking")

    @property
    def logdata_cls(self):
        return MoodLogData

    @property
    def primary_image_url(self) -> str:
        if self.image:
            return self.image.url
        return ""
