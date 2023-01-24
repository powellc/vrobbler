import logging
from datetime import timedelta
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from music.models import Track
from podcasts.models import Episode
from scrobbles.utils import check_scrobble_for_finish
from sports.models import SportEvent
from videos.models import Video

logger = logging.getLogger(__name__)
User = get_user_model()
BNULL = {"blank": True, "null": True}


class Scrobble(TimeStampedModel):
    uuid = models.UUIDField(editable=False, **BNULL)
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, **BNULL)
    track = models.ForeignKey(Track, on_delete=models.DO_NOTHING, **BNULL)
    podcast_episode = models.ForeignKey(
        Episode, on_delete=models.DO_NOTHING, **BNULL
    )
    sport_event = models.ForeignKey(
        SportEvent, on_delete=models.DO_NOTHING, **BNULL
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

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = uuid4()

        return super(Scrobble, self).save(*args, **kwargs)

    @property
    def status(self) -> str:
        if self.is_paused:
            return 'paused'
        if self.played_to_completion:
            return 'finished'
        if self.in_progress:
            return 'in-progress'
        return 'zombie'

    @property
    def percent_played(self) -> int:
        if not self.media_obj.run_time_ticks:
            logger.warning(
                f"{self} has no run_time_ticks value, cannot show percent played"
            )
            return 100

        playback_ticks = self.playback_position_ticks
        if not playback_ticks:
            playback_ticks = (timezone.now() - self.timestamp).seconds * 1000

            if self.played_to_completion:
                playback_ticks = self.media_obj.run_time_ticks

        percent = int((playback_ticks / self.media_obj.run_time_ticks) * 100)
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
        if self.sport_event:
            media_obj = self.sport_event
        return media_obj

    def __str__(self):
        timestamp = self.timestamp.strftime('%Y-%m-%d')
        return f"Scrobble of {self.media_obj} ({timestamp})"

    @classmethod
    def create_or_update_for_video(
        cls, video: "Video", user_id: int, scrobble_data: dict
    ) -> "Scrobble":
        scrobble_data['video_id'] = video.id

        scrobble = (
            cls.objects.filter(
                video=video,
                user_id=user_id,
            )
            .order_by('-modified')
            .first()
        )
        if scrobble and scrobble.percent_played <= 100:
            logger.info(
                f"Found existing scrobble for video {video}, updating",
                {"scrobble_data": scrobble_data},
            )
            return cls.update(scrobble, scrobble_data)

        logger.debug(
            f"No existing scrobble for video {video}, creating",
            {"scrobble_data": scrobble_data},
        )
        # If creating a new scrobble, we don't need status
        scrobble_data.pop('jellyfin_status')
        return cls.create(scrobble_data)

    @classmethod
    def create_or_update_for_track(
        cls, track: "Track", user_id: int, scrobble_data: dict
    ) -> "Scrobble":
        """Look up any existing scrobbles for a track and compare
        the appropriate backoff time for music tracks to the setting
        so we can avoid duplicating scrobbles."""
        scrobble_data['track_id'] = track.id

        scrobble = (
            cls.objects.filter(
                track=track,
                user_id=user_id,
                played_to_completion=False,
            )
            .order_by('-modified')
            .first()
        )
        if scrobble:
            logger.debug(
                f"Found existing scrobble for track {track}, updating",
                {"scrobble_data": scrobble_data},
            )
            return cls.update(scrobble, scrobble_data)

        logger.debug(
            f"No existing scrobble for track {track}, creating",
            {"scrobble_data": scrobble_data},
        )
        # If creating a new scrobble, we don't need status
        scrobble_data.pop('mopidy_status', None)
        scrobble_data.pop('jellyfin_status', None)
        return cls.create(scrobble_data)

    @classmethod
    def create_or_update_for_podcast_episode(
        cls, episode: "Episode", user_id: int, scrobble_data: dict
    ) -> "Scrobble":
        scrobble_data['podcast_episode_id'] = episode.id

        scrobble = (
            cls.objects.filter(
                podcast_episode=episode,
                user_id=user_id,
                played_to_completion=False,
            )
            .order_by('-modified')
            .first()
        )
        if scrobble:
            logger.debug(
                f"Found existing scrobble for podcast {episode}, updating",
                {"scrobble_data": scrobble_data},
            )
            return cls.update(scrobble, scrobble_data)

        logger.debug(
            f"No existing scrobble for podcast epsiode {episode}, creating",
            {"scrobble_data": scrobble_data},
        )
        # If creating a new scrobble, we don't need status
        scrobble_data.pop('mopidy_status')
        return cls.create(scrobble_data)

    @classmethod
    def create_or_update_for_sport_event(
        cls, event: "SportEvent", user_id: int, scrobble_data: dict
    ) -> "Scrobble":
        scrobble_data['sport_event_id'] = event.id
        scrobble = (
            cls.objects.filter(
                sport_event=event,
                user_id=user_id,
                played_to_completion=False,
            )
            .order_by('-modified')
            .first()
        )
        if scrobble:
            logger.debug(
                f"Found existing scrobble for sport event {event}, updating",
                {"scrobble_data": scrobble_data},
            )
            return cls.update(scrobble, scrobble_data)

        logger.debug(
            f"No existing scrobble for sport event {event}, creating",
            {"scrobble_data": scrobble_data},
        )
        # If creating a new scrobble, we don't need status
        scrobble_data.pop('jellyfin_status')
        return cls.create(scrobble_data)

    @classmethod
    def update(cls, scrobble: "Scrobble", scrobble_data: dict) -> "Scrobble":
        # Status is a field we get from Mopidy, which refuses to poll us
        scrobble_status = scrobble_data.pop('mopidy_status', None)
        if not scrobble_status:
            scrobble_status = scrobble_data.pop('jellyfin_status', None)

        logger.debug(f"Scrobbling to {scrobble} with status {scrobble_status}")
        scrobble.update_ticks(scrobble_data)

        # On stop, stop progress and send it to the check for completion
        if scrobble_status == "stopped":
            scrobble.stop()
        # On pause, set is_paused and stop scrobbling
        if scrobble_status == "paused":
            scrobble.pause()
        if scrobble_status == "resumed":
            scrobble.resume()

        for key, value in scrobble_data.items():
            setattr(scrobble, key, value)
        scrobble.save()
        check_scrobble_for_finish(scrobble)
        return scrobble

    @classmethod
    def create(
        cls,
        scrobble_data: dict,
    ) -> "Scrobble":
        scrobble_data['scrobble_log'] = ""
        scrobble = cls.objects.create(
            **scrobble_data,
        )
        return scrobble

    def stop(self, force_finish=False) -> None:
        if not self.in_progress:
            logger.warning("Scrobble already stopped")
            return
        self.in_progress = False
        self.save(update_fields=['in_progress'])
        check_scrobble_for_finish(self, force_finish)

    def pause(self) -> None:
        if self.is_paused:
            logger.warning("Scrobble already paused")
            return
        self.is_paused = True
        self.save(update_fields=["is_paused"])
        check_scrobble_for_finish(self)

    def resume(self) -> None:
        if self.is_paused or not self.in_progress:
            self.is_paused = False
            self.in_progress = True
            return self.save(update_fields=["is_paused", "in_progress"])

    def cancel(self) -> None:
        check_scrobble_for_finish(self, force_finish=True)
        self.delete()

    def update_ticks(self, data) -> None:
        self.playback_position_ticks = data.get("playback_position_ticks")
        self.playback_position = data.get("playback_position")
        logger.debug(
            f"Updating scrobble ticks to {self.playback_position_ticks}"
        )
        self.save(
            update_fields=['playback_position_ticks', 'playback_position']
        )
