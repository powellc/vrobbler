from uuid import uuid4

from django.db import models
from django_extensions.db.models import TimeStampedModel

BNULL = {"blank": True, "null": True}


class ScrobblableMixin(TimeStampedModel):
    SECONDS_TO_STALE = 1600

    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    title = models.CharField(max_length=255, **BNULL)
    run_time = models.CharField(max_length=8, **BNULL)
    run_time_ticks = models.PositiveBigIntegerField(**BNULL)
    # thumbs = models.IntegerField(default=Opinion.NEUTRAL, choices=Opinion.choices)

    class Meta:
        abstract = True
