from uuid import uuid4

from django.apps import apps
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from scrobbles.dataclasses import BeerLogData
from scrobbles.mixins import ScrobblableMixin

BNULL = {"blank": True, "null": True}


class BeerStyle(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    description = models.TextField(**BNULL)


class BeerProducer(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    description = models.TextField(**BNULL)
    location = models.CharField(max_length=255, **BNULL)
    beeradvocate_id = models.CharField(max_length=255, **BNULL)
    untappd_id = models.CharField(max_length=255, **BNULL)

    def find_or_create(cls, title: str) -> "BeerProducer":
        return cls.objects.filter(title=title).first()


class Beer(ScrobblableMixin):
    description = models.TextField(**BNULL)
    ibu = models.SmallIntegerField(**BNULL)
    abv = models.FloatField(**BNULL)
    styles = models.ManyToManyField(BeerStyle, related_name="styles")
    non_alcoholic = models.BooleanField(default=False)
    beeradvocate_id = models.CharField(max_length=255, **BNULL)
    beeradvocate_score = models.SmallIntegerField(**BNULL)
    untappd_image = models.ImageField(upload_to="beers/untappd/", **BNULL)
    untappd_image_small = ImageSpecField(
        source="untappd_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    untappd_image_medium = ImageSpecField(
        source="untappd_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    untappd_id = models.CharField(max_length=255, **BNULL)
    untappd_rating = models.FloatField(**BNULL)
    producer = models.ForeignKey(
        BeerProducer, on_delete=models.DO_NOTHING, **BNULL
    )

    def get_absolute_url(self) -> str:
        return reverse("beers:beer_detail", kwargs={"slug": self.uuid})

    def beeradvocate_link(self):
        if self.producer and self.beeradvocate_id:
            if self.beeradvocate_id:
                link = f"https://www.beeradvocate.com/beer/profile/{self.producer.beeradvocate_id}/{self.beeradvocate_id}/"
        return link

    def untappd_link(self) -> str:
        link = ""
        if self.untappd_id:
            link = f"https://www.untappd.com/beer/{self.untappd_id}/"
        return link

    def primary_image_url(self) -> str:
        url = ""
        if self.beeradvocate_image:
            url = self.beeradvocate_image.url
        return url

    @property
    def logdata_cls(self):
        return BeerLogData

    @classmethod
    def find_or_create(cls, untappd_id: str) -> "Beer":
        return cls.objects.filter(untappd_id=untappd_id).first()

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(
            user_id=user_id, life_event=self
        ).order_by("-timestamp")
