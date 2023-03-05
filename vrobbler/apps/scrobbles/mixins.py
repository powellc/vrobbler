import logging
from typing import Dict
from uuid import uuid4

from django.db import models
from django_extensions.db.models import TimeStampedModel

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
