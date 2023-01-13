import logging
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from music.models import Track
from podcasts.models import Episode
from scrobbles.utils import check_scrobble_for_finish
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
    podcast_episode = models.ForeignKey(
        Episode, on_delete=models.DO_NOTHING, **BNULL
    )
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
        playback_ticks = None
        percent_played = 100

        if not self.media_obj.run_time_ticks:
            logger.warning(
                f"{self} has no run_time_ticks value, cannot show percent played"
            )
            return percent_played

        playback_ticks = self.playback_position_ticks
        if not playback_ticks:
            logger.info(
                "No playback_position_ticks, estimating based on creation time"
            )
            playback_ticks = (timezone.now() - self.timestamp).seconds * 1000

        percent = int((playback_ticks / self.media_obj.run_time_ticks) * 100)

        if percent > 100:
            percent = 100
        return percent

    @property
    def media_obj(self):
        media_obj = None
        if self.video:
            media_obj = self.video
        if self.track:
            media_obj = self.track
        if self.podcast_episode:
            media_obj = self.podcast_episode
        return media_obj

    def __str__(self):
        return f"Scrobble of {self.media_obj} {self.timestamp.year}-{self.timestamp.month}"

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
    def create_or_update_for_podcast_episode(
        cls, episode: "Episode", user_id: int, scrobble_data: dict
    ) -> "Scrobble":
        scrobble_data['podcast_episode_id'] = episode.id
        scrobble = (
            cls.objects.filter(podcast_episode=episode, user_id=user_id)
            .order_by('-modified')
            .first()
        )
        logger.debug(
            f"Found existing scrobble for podcast {episode}, updating",
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
        scrobble_status = scrobble_data.pop('mopidy_status', None)
        if not scrobble_status:
            scrobble_status = scrobble_data.pop('jellyfin_status', None)
        if not scrobble_status:
            logger.warning(
                f"No status update found in message, not scrobbling"
            )
            return

        logger.debug(f"Scrobbling to {scrobble} with status {scrobble_status}")
        if scrobble:
            scrobble.update_ticks(scrobble_data)

            # On stop, stop progress and send it to the check for completion
            if scrobble_status == "stopped":
                return scrobble.stop()

            # On pause, set is_paused and stop scrobbling
            if scrobble_status == "paused":
                return scrobble.pause()

            if scrobble_status == "resumed":
                return scrobble.resume()

            # We're not changing the scrobble, but we don't want to walk over an existing one
            scrobble_is_finished = (
                not scrobble.in_progress and scrobble.modified < backoff
            )
            if scrobble_is_finished:
                logger.info(
                    'Found a very recent scrobble for this item, holding off scrobbling again'
                )
                return

        if not scrobble:
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
        scrobble = check_scrobble_for_finish(scrobble)

        return scrobble

    def stop(self):
        if not self.in_progress:
            logger.warning("Scrobble already stopped")
            return
        self.in_progress = False
        self.save(update_fields=['in_progress'])
        return check_scrobble_for_finish(self)

    def pause(self):
        if self.is_paused:
            logger.warning("Scrobble already paused")
            return
        self.is_paused = True
        self.save(update_fields=["is_paused"])
        return check_scrobble_for_finish(self)

    def resume(self):
        if self.is_paused or not self.in_progress:
            self.is_paused = False
            self.in_progress = True
            return self.save(update_fields=["is_paused", "in_progress"])
        return self

    def update_ticks(self, data):
        self.playback_position_ticks = data.get("playback_position_ticks")
        self.playback_position = data.get("playback_position")
        logger.debug(
            f"Updating scrobble ticks to {self.playback_position_ticks}"
        )
        self.save(
            update_fields=['playback_position_ticks', 'playback_position']
        )
        return self
