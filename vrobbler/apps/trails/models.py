from enum import Enum
from django.apps import apps
from django.db import models
from django.urls import reverse
from scrobbles.dataclasses import TrailLogData
from scrobbles.mixins import ScrobblableMixin
from locations.models import GeoLocation

BNULL = {"blank": True, "null": True}


class TrailType(Enum):
    WOODS = "Woods"
    ROAD = "Road"


class Trail(ScrobblableMixin):
    description = models.TextField(**BNULL)
    trailhead_location = models.ForeignKey(
        GeoLocation,
        related_name="trailheads",
        on_delete=models.DO_NOTHING,
        **BNULL,
    )
    trail_terminus_location = models.ForeignKey(
        GeoLocation,
        related_name="trail_termini",
        on_delete=models.DO_NOTHING,
        **BNULL,
    )
    strava_id = models.CharField(max_length=255, **BNULL)
    trailforks_id = models.CharField(max_length=255, **BNULL)

    def get_absolute_url(self):
        return reverse("trails:trail_detail", kwargs={"slug": self.uuid})

    @property
    def logdata_cls(self):
        return TrailLogData

    @classmethod
    def find_or_create(cls, title: str) -> "Trail":
        return cls.objects.filter(title=title).first()

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(
            user_id=user_id, life_event=self
        ).order_by("-timestamp")
