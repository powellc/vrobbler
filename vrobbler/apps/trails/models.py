from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db import models
from django.urls import reverse
from scrobbles.dataclasses import TrailLogData
from scrobbles.mixins import ScrobblableConstants, ScrobblableMixin
from locations.models import GeoLocation

BNULL = {"blank": True, "null": True}



class Trail(ScrobblableMixin):

    class PrincipalType(models.TextChoices):
        WOODS = "WOODS"
        ROAD = "ROAD"
        BEACH = "BEACH"
        MOUNTAIN = "MOUNTAIN"

    class ActivityType(models.TextChoices):
        WALK= "WALK"
        HIKE = "HIKE"
        RUN = "RUN"
        BIKE = "BIKE"

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
    principal_type = models.CharField(max_length=10, choices=PrincipalType.choices, **BNULL)
    default_activity_type = models.CharField(max_length=10, choices=ActivityType.choices, **BNULL)

    def get_absolute_url(self):
        return reverse("trails:trail_detail", kwargs={"slug": self.uuid})

    @property
    def logdata_cls(self):
        return TrailLogData

    @property
    def strings(self) -> ScrobblableConstants:
        return ScrobblableConstants(verb="Moving", tags="runner")

    @classmethod
    def find_or_create(cls, title: str) -> "Trail":
        return cls.objects.filter(title=title).first()

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(
            user_id=user_id, life_event=self
        ).order_by("-timestamp")
