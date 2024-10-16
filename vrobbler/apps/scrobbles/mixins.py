import logging
from typing import Optional
from uuid import uuid4

from django.apps import apps
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from scrobbles.utils import get_scrobbles_for_media
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

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
    COMPLETION_PERCENT = 100

    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    title = models.CharField(max_length=255, **BNULL)
    run_time_seconds = models.IntegerField(**BNULL)
    run_time_ticks = models.PositiveBigIntegerField(**BNULL)

    genre = TaggableManager(through=ObjectWithGenres, blank=True)

    class Meta:
        abstract = True

    def scrobble_for_user(
        self,
        user_id,
        source: str = "Vrobbler",
        playback_position_seconds: int = 0,
        status: str = "started",
        log: Optional[dict] = None,
    ):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        scrobble_data = {
            "user_id": user_id,
            "timestamp": timezone.now(),
            "source": source,
            "playback_position_seconds": playback_position_seconds,
            "status": status,
            "log": log,
        }

        logger.info(
            "[scrobble_for_user] called",
            extra={
                "id": self.id,
                "media_type": self.__class__,
                "user_id": user_id,
                "scrobble_data": scrobble_data,
                "media_type": Scrobble.MediaType.WEBPAGE,
            },
        )
        return Scrobble.create_or_update(self, user_id, scrobble_data)

    def get_start_url(self):
        return reverse("scrobbles:start", kwargs={"uuid": self.uuid})

    @property
    def primary_image_url(self) -> str:
        logger.warning(f"Not implemented yet")
        return ""

    @property
    def logdata_cls(self) -> None:
        from scrobbles.dataclasses import ScrobbleLogData
        return ScrobbleLogData

    @property
    def subtitle(self) -> str:
        return ""

    def fix_metadata(self) -> None:
        logger.warning("fix_metadata() not implemented yet")

    @classmethod
    def find_or_create(cls) -> None:
        logger.warning("find_or_create() not implemented yet")

    def __str__(self):
        if self.title:
            return self.title
        return str(self.uuid)


class LongPlayScrobblableMixin(ScrobblableMixin):
    class Meta:
        abstract = True

    def get_longplay_finish_url(self):
        return reverse("scrobbles:longplay-finish", kwargs={"uuid": self.uuid})

    def first_long_play_scrobble_for_user(self, user) -> Optional["Scrobble"]:
        return (
            get_scrobbles_for_media(self, user)
            .filter(
                log__long_play_complete=False,
                log__serial_scrobble_id__isnull=True,
            )
            .order_by("timestamp")
            .first()
        )

    def last_long_play_scrobble_for_user(self, user) -> Optional["Scrobble"]:
        return (
            get_scrobbles_for_media(self, user)
            .filter(
                log__long_play_complete=False,
                log__serial_scrobble_id__isnull=False,
            )
            .order_by("timestamp")
            .last()
        )
