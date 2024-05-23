from django.apps import apps
from django.db import models
from django.urls import reverse
import pendulum
from lifeevents.dataclasses import LifeEventMetadata
from scrobbles.mixins import ScrobblableMixin

BNULL = {"blank": True, "null": True}


class LifeEvent(ScrobblableMixin):
    COMPLETION_PERCENT = 100

    description = models.TextField(**BNULL)

    def get_absolute_url(self):
        return reverse(
            "life-events:life-event_detail", kwargs={"slug": self.uuid}
        )

    @property
    def metadata_class(self):
        return LifeEventMetadata

    @classmethod
    def find_or_create(cls, title: str) -> "LifeEvent":
        return cls.objects.filter(title=title).first()

    def scrobble_for_user(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.create(
            user_id=user_id, life_event=self, timestamp=pendulum.now()
        )

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(
            user_id=user_id, life_event=self
        ).order_by("-timestamp")
