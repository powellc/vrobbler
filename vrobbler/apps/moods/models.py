import logging
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from scrobbles.mixins import ScrobblableMixin
from vrobbler.apps.scrobbles.dataclasses import MoodLogData

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}
User = get_user_model()


class Mood(ScrobblableMixin):
    description = models.TextField(**BNULL)

    def __str__(self):
        if self.title:
            return self.title
        return str(self.uuid)

    def get_absolute_url(self):
        return reverse("moods:mood-detail", kwargs={"slug": self.uuid})

    @property
    def logdata_cls(self):
        return MoodLogData
