import logging
from typing import Optional
from uuid import uuid4

from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from taggit.managers import TaggableManager
from scrobbles.utils import get_scrobbles_for_media
from taggit.models import TagBase, GenericTaggedItemBase

BNULL = {"blank": True, "null": True}

logger = logging.getLogger(__name__)


class Genre(TagBase):
    source = models.CharField(max_length=255, **BNULL)

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"


class ObjectWithGenres(GenericTaggedItemBase):
    tag = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
        **BNULL,
    )


class ScrobblableMixin(TimeStampedModel):
    SECONDS_TO_STALE = 1600

    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    title = models.CharField(max_length=255, **BNULL)
    run_time_seconds = models.IntegerField(**BNULL)
    run_time_ticks = models.PositiveBigIntegerField(**BNULL)

    genre = TaggableManager(through=ObjectWithGenres, blank=True)

    class Meta:
        abstract = True

    @property
    def primary_image_url(self) -> str:
        logger.warn(f"Not implemented yet")
        return ""

    def fix_metadata(self):
        logger.warn("fix_metadata() not implemented yet")

    @classmethod
    def find_or_create(cls):
        logger.warn("find_or_create() not implemented yet")

    def scrobble(self, user_id, **kwargs):
        """Given a user ID and a dictionary of data, attempts to scrobble it"""
        from scrobbles.models import Scrobble
        Scrobble.create_or_update(self, user_id, **kwargs)


class LongPlayScrobblableMixin(ScrobblableMixin):
    class Meta:
        abstract = True

    def get_longplay_finish_url(self):
        return reverse("scrobbles:longplay-finish", kwargs={"uuid": self.uuid})

    def last_long_play_scrobble_for_user(self, user) -> Optional["Scrobble"]:
        return (
            get_scrobbles_for_media(self, user)
            .filter(long_play_complete=False)
            .order_by("-timestamp")
            .first()
        )
