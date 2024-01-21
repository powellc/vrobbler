import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

import requests
from boardgames.bgg import lookup_boardgame_from_bgg
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from scrobbles.mixins import ScrobblableMixin
from vrobbler.apps.boardgames.bgg import lookup_boardgame_id_from_bgg

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class BoardGamePublisher(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    logo = models.ImageField(upload_to="games/platform-logos/", **BNULL)
    igdb_id = models.IntegerField(**BNULL)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "boardgames:publisher_detail", kwargs={"slug": self.uuid}
        )


class BoardGame(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(
        settings, "BOARD_GAME_COMPLETION_PERCENT", 100
    )

    FIELDS_FROM_BGGEEK = [
        "igdb_id",
        "alternative_name",
        "rating",
        "rating_count",
        "release_date",
        "cover",
        "screenshot",
    ]

    title = models.CharField(max_length=255)
    publisher = models.ForeignKey(
        BoardGamePublisher, **BNULL, on_delete=models.DO_NOTHING
    )
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    description = models.TextField(**BNULL)
    cover = models.ImageField(upload_to="boardgames/covers/", **BNULL)
    cover_small = ImageSpecField(
        source="cover",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    cover_medium = ImageSpecField(
        source="cover",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    layout_image = models.ImageField(upload_to="boardgames/layouts/", **BNULL)
    layout_image_small = ImageSpecField(
        source="layout_image",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    layout_image_medium = ImageSpecField(
        source="layout_image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    rating = models.FloatField(**BNULL)
    max_players = models.PositiveSmallIntegerField(**BNULL)
    min_players = models.PositiveSmallIntegerField(**BNULL)
    published_date = models.DateField(**BNULL)
    recommended_age = models.PositiveSmallIntegerField(**BNULL)
    bggeek_id = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "boardgames:boardgame_detail", kwargs={"slug": self.uuid}
        )

    def primary_image_url(self) -> str:
        url = ""
        if self.cover:
            url = self.cover.url
        return url

    def bggeek_link(self):
        link = ""
        if self.bggeek_id:
            link = f"https://boardgamegeek.com/boardgame/{self.bggeek_id}"
        return link

    def get_start_url(self):
        return reverse("scrobbles:start", kwargs={"uuid": self.uuid})

    def fix_metadata(self, data: dict = {}, force_update=False) -> None:

        if not self.published_date or force_update:

            if not data:
                data = lookup_boardgame_from_bgg(str(self.bggeek_id))

            cover_url = data.pop("cover_url")
            year = data.pop("year_published")
            publisher_name = data.pop("publisher_name")

            if year:
                data["published_date"] = datetime(int(year), 1, 1)

            # Fun trick for updating all fields at once
            BoardGame.objects.filter(pk=self.id).update(**data)
            self.refresh_from_db()

            # Add publishers
            (
                self.publisher,
                _created,
            ) = BoardGamePublisher.objects.get_or_create(name=publisher_name)
            self.save()

            # Go get cover image if the URL is present
            if cover_url and not self.cover:
                headers = {"User-Agent": "Vrobbler 0.11.12"}
                r = requests.get(cover_url, headers=headers)
                logger.debug(r.status_code)
                if r.status_code == 200:
                    fname = f"{self.title}_cover_{self.uuid}.jpg"
                    self.cover.save(fname, ContentFile(r.content), save=True)
                    logger.debug("Loaded cover image from BGGeek")

    @classmethod
    def find_or_create(
        cls, lookup_id: str, data: Optional[dict] = {}
    ) -> Optional["BoardGame"]:
        """Given a Lookup ID (either BGG or BGA ID), return a board game object"""
        boardgame = cls.objects.filter(bggeek_id=lookup_id).first()

        if not data or not boardgame:
            data = lookup_boardgame_from_bgg(lookup_id)

        if data and not boardgame:
            boardgame, created = cls.objects.get_or_create(
                title=data["title"], bggeek_id=lookup_id
            )
            if created:
                boardgame.fix_metadata(data=data)

        return boardgame
