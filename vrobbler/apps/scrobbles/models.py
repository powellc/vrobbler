import logging
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from music.models import Track
from videos.models import Video

logger = logging.getLogger(__name__)
User = get_user_model()
BNULL = {"blank": True, "null": True}
VIDEO_BACKOFF = getattr(settings, 'VIDEO_BACKOFF_MINUTES')
TRACK_BACKOFF = getattr(settings, 'MUSIC_BACKOFF_SECONDS')
VIDEO_WAIT_PERIOD = getattr(settings, 'VIDEO_WAIT_PERIOD_DAYS')
TRACK_WAIT_PERIOD = getattr(settings, 'MUSIC_WAIT_PERIOD_MINUTES')


class Scrobble(TimeStampedModel):
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, **BNULL)
    track = models.ForeignKey(Track, on_delete=models.DO_NOTHING, **BNULL)
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
        if self.playback_position_ticks and self.media_run_time_ticks:
            return int(
                (self.playback_position_ticks / self.media_run_time_ticks)
                * 100
            )
        # If we don't have media_run_time_ticks, let's guess from created time
        now = timezone.now()
        playback_duration = (now - self.created).seconds
        if playback_duration and self.track.run_time:
            return int((playback_duration / int(self.track.run_time)) * 100)

        return 0

    @property
    def media_run_time_ticks(self) -> int:
        if self.video:
            return self.video.run_time_ticks
        if self.track:
            return self.track.run_time_ticks
        # this is hacky, but want to avoid divide by zero
        return 1

    def is_stale(self, backoff, wait_period) -> bool:
        scrobble_is_stale = self.in_progress and self.modified > wait_period

        # Check if found in progress scrobble is more than a day old
        if scrobble_is_stale:
            logger.info(
                'Found a in-progress scrobble for this item more than a day old, creating a new scrobble'
            )
            delete_stale_scrobbles = getattr(
                settings, "DELETE_STALE_SCROBBLES", True
            )

            if delete_stale_scrobbles:
                logger.info(
                    'Deleting {scrobble} that has been in-progress too long'
                )
                self.delete()

        return scrobble_is_stale

    def __str__(self):
        media = None
        if self.video:
            media = self.video
        if self.track:
            media = self.track

        return (
            f"Scrobble of {media} {self.timestamp.year}-{self.timestamp.month}"
        )

    @classmethod
    def create_or_update_for_video(
        cls, video: "Video", user_id: int, jellyfin_data: dict
    ) -> "Scrobble":
        jellyfin_data['video_id'] = video.id
        logger.debug(
            f"Creating or updating scrobble for video {video} with data {jellyfin_data}"
        )
        scrobble = (
            cls.objects.filter(video=video, user_id=user_id)
            .order_by('-modified')
            .first()
        )

        # Backoff is how long until we consider this a new scrobble
        backoff = timezone.now() + timedelta(minutes=VIDEO_BACKOFF)
        wait_period = timezone.now() + timedelta(days=VIDEO_WAIT_PERIOD)

        return cls.update_or_create(
            scrobble, backoff, wait_period, jellyfin_data
        )

    @classmethod
    def create_or_update_for_track(
        cls, track: "Track", user_id: int, scrobble_data: dict
    ) -> "Scrobble":
        scrobble_data['track_id'] = track.id
        scrobble = (
            cls.objects.filter(track=track, user_id=user_id)
            .order_by('-modified')
            .first()
        )
        logger.debug(
            f"Found existing scrobble for track {track}, updating",
            {"scrobble_data": scrobble_data},
        )

        backoff = timezone.now() + timedelta(seconds=TRACK_BACKOFF)
        wait_period = timezone.now() + timedelta(minutes=TRACK_WAIT_PERIOD)

        return cls.update_or_create(
            scrobble, backoff, wait_period, scrobble_data
        )

    @classmethod
    def update_or_create(
        cls,
        scrobble: Optional["Scrobble"],
        backoff,
        wait_period,
        scrobble_data: dict,
    ) -> Optional["Scrobble"]:

        # Status is a field we get from Mopidy, which refuses to poll us
        mopidy_status = scrobble_data.pop('status', None)
        scrobble_is_stale = False

        if mopidy_status == "stopped":
            logger.info(f"Mopidy sent a message to stop {scrobble}")
            if not scrobble:
                logger.warning(
                    'Mopidy sent us a stopped message, without ever starting'
                )
                return

            # Mopidy finished a play, scrobble away
            scrobble.in_progress = False
            scrobble.save(update_fields=['in_progress'])
            return scrobble

        if scrobble and not mopidy_status:
            scrobble_is_finished = (
                not scrobble.in_progress and scrobble.modified < backoff
            )
            if scrobble_is_finished:
                logger.info(
                    'Found a very recent scrobble for this item, holding off scrobbling again'
                )
                return

            scrobble_is_stale = scrobble.is_stale(backoff, wait_period)

        if (not scrobble or scrobble_is_stale) or mopidy_status:
            # If we default this to "" we can probably remove this
            scrobble_data['scrobble_log'] = ""
            scrobble = cls.objects.create(
                **scrobble_data,
            )
        else:
            for key, value in scrobble_data.items():
                setattr(scrobble, key, value)
            scrobble.save()

        # If we hit our completion threshold, save it and get ready
        # to scrobble again if we re-watch this.
        if scrobble.percent_played >= getattr(
            settings, "PERCENT_FOR_COMPLETION", 95
        ):
            scrobble.in_progress = False
            scrobble.playback_position_ticks = scrobble.media_run_time_ticks
            scrobble.save()

        if scrobble.percent_played % 5 == 0:
            if getattr(settings, "KEEP_DETAILED_SCROBBLE_LOGS", False):
                scrobble.scrobble_log += f"\n{str(scrobble.timestamp)} - {scrobble.playback_position} - {str(scrobble.playback_position_ticks)} - {str(scrobble.percent_played)}%"
                scrobble.save(update_fields=['scrobble_log'])

        return scrobble
