from uuid import uuid4

from beers.untappd import get_beer_from_untappd_id, get_rating_from_soup
from django.apps import apps
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from scrobbles.dataclasses import BeerLogData
from scrobbles.mixins import ScrobblableConstants, ScrobblableMixin

BNULL = {"blank": True, "null": True}


class BeerStyle(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    description = models.TextField(**BNULL)

    def __str__(self):
        return self.name


class BeerProducer(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    description = models.TextField(**BNULL)
    location = models.CharField(max_length=255, **BNULL)
    beeradvocate_id = models.CharField(max_length=255, **BNULL)
    untappd_id = models.CharField(max_length=255, **BNULL)

    def find_or_create(cls, title: str) -> "BeerProducer":
        return cls.objects.filter(title=title).first()

    def __str__(self):
        return self.name


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

    @property
    def subtitle(self):
        return self.producer.name

    @property
    def strings(self) -> ScrobblableConstants:
        return ScrobblableConstants(verb="Drinking", tags="beer")

    @property
    def beeradvocate_link(self) -> str:
        link = ""
        if self.producer and self.beeradvocate_id:
            if self.beeradvocate_id:
                link = f"https://www.beeradvocate.com/beer/profile/{self.producer.beeradvocate_id}/{self.beeradvocate_id}/"
        return link

    @property
    def untappd_link(self) -> str:
        link = ""
        if self.untappd_id:
            link = f"https://www.untappd.com/beer/{self.untappd_id}/"
        return link

    @property
    def primary_image_url(self) -> str:
        url = ""
        if self.untappd_image:
            url = self.untappd_image.url
        return url

    @property
    def logdata_cls(self):
        return BeerLogData

    @classmethod
    def find_or_create(cls, untappd_id: str) -> "Beer":
        beer = cls.objects.filter(untappd_id=untappd_id).first()

        if not beer:
            beer_dict = get_beer_from_untappd_id(untappd_id)
            producer_dict = {}
            style_ids = []
            for key in list(beer_dict.keys()):
                if "producer__" in key:
                    pkey = key.replace("producer__", "")
                    producer_dict[pkey] = beer_dict.pop(key)
                if "styles" in key:
                    for style in beer_dict.pop("styles"):
                        style_inst, created = BeerStyle.objects.get_or_create(
                            name=style
                        )
                        style_ids.append(style_inst.id)

            producer, _created = BeerProducer.objects.get_or_create(
                **producer_dict
            )
            beer_dict["producer_id"] = producer.id
            beer = Beer.objects.create(**beer_dict)
            for style_id in style_ids:
                beer.styles.add(style_id)

        return beer

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(
            user_id=user_id, life_event=self
        ).order_by("-timestamp")
