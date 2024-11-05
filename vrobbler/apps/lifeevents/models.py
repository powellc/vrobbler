from django.apps import apps
from django.db import models
from django.urls import reverse
from scrobbles.dataclasses import LifeEventLogData
from scrobbles.mixins import ScrobblableConstants, ScrobblableMixin

BNULL = {"blank": True, "null": True}


class LifeEvent(ScrobblableMixin):
    description = models.TextField(**BNULL)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "life-events:life-event_detail", kwargs={"slug": self.uuid}
        )

    @property
    def logdata_cls(self):
        return LifeEventLogData

    @property
    def strings(self) -> ScrobblableConstants:
        return ScrobblableConstants(verb="Experiencing", tags="camping")

    @classmethod
    def find_or_create(cls, title: str) -> "LifeEvent":
        return cls.objects.filter(title=title).first()

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(
            user_id=user_id, life_event=self
        ).order_by("-timestamp")
