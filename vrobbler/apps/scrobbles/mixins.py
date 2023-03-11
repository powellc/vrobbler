import logging
from typing import Optional
from uuid import uuid4

from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from scrobbles.utils import get_scrobbles_for_media

BNULL = {"blank": True, "null": True}

logger = logging.getLogger(__name__)


class ScrobblableMixin(TimeStampedModel):
    SECONDS_TO_STALE = 1600

    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    title = models.CharField(max_length=255, **BNULL)
    run_time = models.CharField(max_length=8, **BNULL)
    run_time_ticks = models.PositiveBigIntegerField(**BNULL)

    class Meta:
        abstract = True

    def fix_metadata(self):
        logger.warn("fix_metadata() not implemented yet")

    @classmethod
    def find_or_create(cls):
        logger.warn("find_or_create() not implemented yet")


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
