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
    playback_position_ticks = models.PositiveIntegerField(**BNULL)
    playback_position = models.CharField(max_length=8, **BNULL)
    is_paused = models.BooleanField(default=False)
    played_to_completion = models.BooleanField(default=False)
    source = models.CharField(max_length=255, **BNULL)
    source_id = models.TextField(**BNULL)

    def percent_played(self):
        return int((self.playback_position_ticks / video.run_time_ticks) * 100)
