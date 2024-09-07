from django.apps import apps
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from scrobbles.dataclasses import BrickSetLogData
from scrobbles.mixins import LongPlayScrobblableMixin

BNULL = {"blank": True, "null": True}


class BrickSet(LongPlayScrobblableMixin):
    """"""

    number = models.CharField(max_length=10, **BNULL)
    release_year = models.IntegerField(**BNULL)
    piece_count = models.IntegerField(**BNULL)
    brickset_rating = models.DecimalField(max_digits=3, decimal_places=1, **BNULL)
    lego_item_number = models.CharField(max_length=10, **BNULL)
    box_image = models.ImageField(upload_to="brickset/boxes/", **BNULL)
    box_image_small = ImageSpecField(
        source="box_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    box_image_medium = ImageSpecField(
        source="box_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    set_image = models.ImageField(upload_to="brickset/sets/", **BNULL)
    set_image_small = ImageSpecField(
        source="set_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    set_image_medium = ImageSpecField(
        source="set_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )

    def get_absolute_url(self):
        return reverse("bricksets:brickset_detail", kwargs={"slug": self.uuid})

    @property
    def logdata_cls(self):
        return BrickSetLogData

    @classmethod
    def find_or_create(cls, title: str) -> "BrickSet":
        return cls.objects.filter(title=title).first()

    @property
    def primary_image_url(self) -> str:
        if self.box_image:
            return self.box_image.url
        return ""
