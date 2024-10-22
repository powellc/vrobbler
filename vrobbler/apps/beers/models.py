from django.apps import apps
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from scrobbles.dataclasses import BeerLogData
from scrobbles.mixins import ScrobblableMixin

BNULL = {"blank": True, "null": True}


class BeerProducer(TimeStampedModel):
    description = models.TextField(**BNULL)
    location = models.CharField(max_length=255, **BNULL)


class Beer(ScrobblableMixin):
    description = models.TextField(**BNULL)
    ibu = models.SmallIntegerField(**BNULL)
    abv = models.FloatField(**BNULL)
    style = models.CharField(max_length=100, **BNULL)
    non_alcoholic = models.BooleanField(default=False)
    beeradvocate_id = models.CharField(max_length=255, **BNULL)
    beeradvocate_score = models.SmallIntegerField(**BNULL)
    untappd_id = models.CharField(max_length=255, **BNULL)

    def get_absolute_url(self):
        return reverse("beers:beer_detail", kwargs={"slug": self.uuid})

    @property
    def logdata_cls(self):
        return BeerLogData

    @classmethod
    def find_or_create(cls, title: str) -> "Beer":
        return cls.objects.filter(title=title).first()

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(
            user_id=user_id, life_event=self
        ).order_by("-timestamp")
