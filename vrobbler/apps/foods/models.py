from uuid import uuid4

from django.apps import apps
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from scrobbles.dataclasses import FoodLogData
from scrobbles.mixins import ScrobblableConstants, ScrobblableMixin

BNULL = {"blank": True, "null": True}


class FoodCategory(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    allrecipe_image = models.ImageField(upload_to="food/recipe/", **BNULL)
    allrecipe_image_small = ImageSpecField(
        source="recipe_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    allrecipe_image_medium = ImageSpecField(
        source="recipe_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    allrecipe_id = models.CharField(max_length=255, **BNULL)
    description = models.TextField(**BNULL)

    def find_or_create(cls, title: str) -> "FoodCategory":
        return cls.objects.filter(title=title).first()

    def __str__(self):
        return self.name


class Food(ScrobblableMixin):
    description = models.TextField(**BNULL)
    allrecipe_image = models.ImageField(upload_to="food/recipe/", **BNULL)
    allrecipe_image_small = ImageSpecField(
        source="recipe_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    allrecipe_image_medium = ImageSpecField(
        source="recipe_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    allrecipe_id = models.CharField(max_length=255, **BNULL)
    allrecipe_rating = models.FloatField(**BNULL)
    category = models.ForeignKey(
        FoodCategory, on_delete=models.DO_NOTHING, **BNULL
    )

    def get_absolute_url(self) -> str:
        return reverse("foods:food_detail", kwargs={"slug": self.uuid})

    @property
    def subtitle(self):
        return self.category.name

    @property
    def strings(self) -> ScrobblableConstants:
        return ScrobblableConstants(verb="Eating", tags="food")

    @property
    def allrecipe_link(self) -> str:
        link = ""
        if self.producer and self.allrecipe_id:
            if self.allrecipe_id:
                link = f"https://www.allrecipe.com/{self.allrecipe_id}/"
        return link

    @property
    def primary_image_url(self) -> str:
        url = ""
        if self.allrecipe_image:
            url = self.allrecipe_image.url
        return url

    @property
    def logdata_cls(self):
        return FoodLogData

    @classmethod
    def find_or_create(cls, allrecipe_id: str) -> "Food":
        food = cls.objects.filter(allrecipe_id=allrecipe_id).first()

        if not food:
            food_dict = get_food_from_allrecipe_id(allrecipe_id)
            # category_dict = {}

            # category, _created = FoodCategory.objects.get_or_create(
            #    **category_dict
            # )
            food = Food.objects.create(**food_dict)
            # for category_id in category_ids:
            #    food.category.add(category_id)

        return food

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(user_id=user_id, food=self).order_by(
            "-timestamp"
        )
