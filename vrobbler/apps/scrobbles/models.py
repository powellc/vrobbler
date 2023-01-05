from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import TimeStampedModel

from videos.models import Video

User = get_user_model()
BNULL = {"blank": True, "null": True}


class Scrobble(TimeStampedModel):
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    timestamp = models.DateTimeField(**BNULL)
    playback_position_ticks = models.PositiveBigIntegerField(**BNULL)
    playback_position = models.CharField(max_length=8, **BNULL)
    is_paused = models.BooleanField(default=False)
    played_to_completion = models.BooleanField(default=False)
    source = models.CharField(max_length=255, **BNULL)
    source_id = models.TextField(**BNULL)
    in_progress = models.BooleanField(default=True)
    scrobble_log = models.TextField(**BNULL)

    @property
    def percent_played(self) -> int:
        return int(
            (self.playback_position_ticks / self.video.run_time_ticks) * 100
        )

    def __str__(self):
        return f"Scrobble of {self.video} {self.timestamp.year}-{self.timestamp.month}"
