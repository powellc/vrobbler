import calendar
import logging
from uuid import uuid4

from books.models import Book
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from music.models import Artist, Track
from podcasts.models import Episode
from scrobbles.lastfm import LastFM
from scrobbles.utils import check_scrobble_for_finish
from sports.models import SportEvent
from videos.models import Series, Video

from vrobbler.apps.scrobbles.stats import build_charts

logger = logging.getLogger(__name__)
User = get_user_model()
BNULL = {"blank": True, "null": True}


class BaseFileImportMixin(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, **BNULL)
    uuid = models.UUIDField(editable=False, default=uuid4)
    processing_started = models.DateTimeField(**BNULL)
    processed_finished = models.DateTimeField(**BNULL)
    process_log = models.TextField(**BNULL)
    process_count = models.IntegerField(**BNULL)

    class Meta:
        abstract = True

    def __str__(self):
        return f"Scrobble import {self.id}"

    @property
    def human_start(self):
        start = "Unknown"
        if self.processing_started:
            start = self.processing_started.strftime('%B %d, %Y at %H:%M')
        return start

    @property
    def import_type(self) -> str:
        class_name = self.__class__.__name__
        if class_name == 'AudioscrobblerTSVImport':
            return "Audioscrobbler"
        if class_name == 'KoReaderImport':
            return "KoReader"
        if self.__class__.__name__ == 'LastFMImport':
            return "LastFM"
        return "Generic"

    def process(self, force=False):
        logger.warning("Process not implemented")

    def undo(self, dryrun=False):
        """Accepts the log from a scrobble import and removes the scrobbles"""
        from scrobbles.models import Scrobble

        if not self.process_log:
            logger.warning("No lines in process log found to undo")
            return

        for line in self.process_log.split('\n'):
            scrobble_id = line.split("\t")[0]
            scrobble = Scrobble.objects.filter(id=scrobble_id).first()
            if not scrobble:
                logger.warning(
                    f"Could not find scrobble {scrobble_id} to undo"
                )
                continue
            logger.info(f"Removing scrobble {scrobble_id}")
            if not dryrun:
                scrobble.delete()
        self.processed_finished = None
        self.processing_started = None
        self.process_count = None
        self.process_log = ""
        self.save(
            update_fields=[
                "processed_finished",
                "processing_started",
                "process_log",
                "process_count",
            ]
        )

    def mark_started(self):
        self.processing_started = timezone.now()
        self.save(update_fields=["processing_started"])

    def mark_finished(self):
        self.processed_finished = timezone.now()
        self.save(update_fields=['processed_finished'])

    def record_log(self, scrobbles):
        self.process_log = ""
        if not scrobbles:
            self.process_count = 0
            self.save(update_fields=["process_log", "process_count"])
            return

        for count, scrobble in enumerate(scrobbles):
            scrobble_str = f"{scrobble.id}\t{scrobble.timestamp}\t{scrobble.media_obj.title}"
            log_line = f"{scrobble_str}"
            if count > 0:
                log_line = "\n" + log_line
            self.process_log += log_line
        self.process_count = len(scrobbles)
        self.save(update_fields=["process_log", "process_count"])


class KoReaderImport(BaseFileImportMixin):
    class Meta:
        verbose_name = "KOReader Import"

    def __str__(self):
        return f"KoReader import on {self.human_start}"

    def get_absolute_url(self):
        return reverse(
            'scrobbles:koreader-import-detail', kwargs={'slug': self.uuid}
        )

    def get_path(instance, filename):
        extension = filename.split('.')[-1]
        uuid = instance.uuid
        return f'koreader-uploads/{uuid}.{extension}'

    sqlite_file = models.FileField(upload_to=get_path, **BNULL)

    def process(self, force=False):
        from scrobbles.koreader import process_koreader_sqlite_file

        if self.processed_finished and not force:
            logger.info(
                f"{self} already processed on {self.processed_finished}"
            )
            return

        self.mark_started()
        scrobbles = process_koreader_sqlite_file(
            self.sqlite_file.path, self.user.id
        )
        self.record_log(scrobbles)
        self.mark_finished()


class AudioScrobblerTSVImport(BaseFileImportMixin):
    class Meta:
        verbose_name = "AudioScrobbler TSV Import"

    def __str__(self):
        return f"Audioscrobbler import on {self.human_start}"

    def get_absolute_url(self):
        return reverse(
            'scrobbles:tsv-import-detail', kwargs={'slug': self.uuid}
        )

    def get_path(instance, filename):
        extension = filename.split('.')[-1]
        uuid = instance.uuid
        return f'audioscrobbler-uploads/{uuid}.{extension}'

    tsv_file = models.FileField(upload_to=get_path, **BNULL)

    def process(self, force=False):
        from scrobbles.tsv import process_audioscrobbler_tsv_file

        if self.processed_finished and not force:
            logger.info(
                f"{self} already processed on {self.processed_finished}"
            )
            return

        self.mark_started()

        tz = None
        if self.user:
            tz = self.user.profile.tzinfo
        scrobbles = process_audioscrobbler_tsv_file(
            self.tsv_file.path, self.user.id, user_tz=tz
        )
        self.record_log(scrobbles)
        self.mark_finished()


class LastFmImport(BaseFileImportMixin):
    class Meta:
        verbose_name = "Last.FM Import"

    def __str__(self):
        return f"LastFM import on {self.human_start}"

    def get_absolute_url(self):
        return reverse(
            'scrobbles:lastfm-import-detail', kwargs={'slug': self.uuid}
        )

    def process(self, import_all=False):
        """Import scrobbles found on LastFM"""
        if self.processed_finished:
            logger.info(
                f"{self} already processed on {self.processed_finished}"
            )
            return

        last_import = None
        if not import_all:
            try:
                last_import = LastFmImport.objects.exclude(id=self.id).last()
            except:
                pass

        if not import_all and not last_import:
            logger.warn(
                "No previous import, to import all Last.fm scrobbles, pass import_all=True"
            )
            return

        lastfm = LastFM(self.user)
        last_processed = None
        if last_import:
            last_processed = last_import.processed_finished

        self.mark_started()

        scrobbles = lastfm.import_from_lastfm(last_processed)

        self.record_log(scrobbles)
        self.mark_finished()


class ChartRecord(TimeStampedModel):
    """Sort of like a materialized view for what we could dynamically generate,
    but would kill the DB as it gets larger. Collects time-based records
    generated by a cron-like archival job

    1972 by Josh Rouse - #3 in 2023, January

    """

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, **BNULL)
    rank = models.IntegerField()
    count = models.IntegerField(default=0)
    year = models.IntegerField(default=timezone.now().year)
    month = models.IntegerField(**BNULL)
    week = models.IntegerField(**BNULL)
    day = models.IntegerField(**BNULL)
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, **BNULL)
    series = models.ForeignKey(Series, on_delete=models.DO_NOTHING, **BNULL)
    artist = models.ForeignKey(Artist, on_delete=models.DO_NOTHING, **BNULL)
    track = models.ForeignKey(Track, on_delete=models.DO_NOTHING, **BNULL)

    @property
    def media_obj(self):
        media_obj = None
        if self.video:
            media_obj = self.video
        if self.track:
            media_obj = self.track
        if self.artist:
            media_obj = self.artist
        return media_obj

    @property
    def month_str(self) -> str:
        month_str = ""
        if self.month:
            month_str = calendar.month_name[self.month]
        return month_str

    @property
    def day_str(self) -> str:
        day_str = ""
        if self.day:
            day_str = str(self.day)
        return day_str

    @property
    def week_str(self) -> str:
        week_str = ""
        if self.week:
            week_str = str(self.week)
        return "Week " + week_str

    @property
    def period(self) -> str:
        period = str(self.year)
        if self.month:
            period = " ".join([self.month_str, period])
        if self.week:
            period = " ".join([self.week_str, period])
        if self.day:
            period = " ".join([self.day_str, period])
        return period

    @property
    def period_type(self) -> str:
        period = 'year'
        if self.month:
            period = 'month'
        if self.week:
            period = 'week'
        if self.day:
            period = 'day'
        return period

    def __str__(self):
        title = f"#{self.rank} in {self.period}"
        if self.day or self.week:
            title = f"#{self.rank} on {self.period}"
        return title

    def link(self):
        get_params = f"?date={self.year}"
        if self.week:
            get_params = get_params = get_params + f"-W{self.week}"
        if self.month:
            get_params = get_params = get_params + f"-{self.month}"
        if self.day:
            get_params = get_params = get_params + f"-{self.day}"
        if self.artist:
            get_params = get_params + "&media=Artist"
        return reverse('scrobbles:charts-home') + get_params

    @classmethod
    def build(cls, user, **kwargs):
        build_charts(user=user, **kwargs)

    @classmethod
    def for_year(cls, user, year):
        return cls.objects.filter(year=year, user=user)

    @classmethod
    def for_month(cls, user, year, month):
        return cls.objects.filter(year=year, month=month, user=user)

    @classmethod
    def for_day(cls, user, year, day, month):
        return cls.objects.filter(year=year, month=month, day=day, user=user)

    @classmethod
    def for_week(cls, user, year, week):
        return cls.objects.filter(year=year, week=week, user=user)


class Scrobble(TimeStampedModel):
    """A scrobble tracks played media items by a user."""

    uuid = models.UUIDField(editable=False, **BNULL)
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, **BNULL)
    track = models.ForeignKey(Track, on_delete=models.DO_NOTHING, **BNULL)
    podcast_episode = models.ForeignKey(
        Episode, on_delete=models.DO_NOTHING, **BNULL
    )
    sport_event = models.ForeignKey(
        SportEvent, on_delete=models.DO_NOTHING, **BNULL
    )
    book = models.ForeignKey(Book, on_delete=models.DO_NOTHING, **BNULL)
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.DO_NOTHING
    )

    # Time keeping
    timestamp = models.DateTimeField(**BNULL)
    playback_position_ticks = models.PositiveBigIntegerField(**BNULL)
    playback_position = models.CharField(max_length=8, **BNULL)

    # Status indicators
    is_paused = models.BooleanField(default=False)
    played_to_completion = models.BooleanField(default=False)
    in_progress = models.BooleanField(default=True)

    # Metadata
    source = models.CharField(max_length=255, **BNULL)
    source_id = models.TextField(**BNULL)
    scrobble_log = models.TextField(**BNULL)

    # Fields for keeping track of reads between scrobbles
    book_pages_read = models.IntegerField(**BNULL)

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
    def is_stale(self) -> bool:
        """Mark scrobble as stale if it's been more than an hour since it was updated"""
        is_stale = False
        now = timezone.now()
        seconds_since_last_update = (now - self.modified).seconds
        if seconds_since_last_update >= self.media_obj.SECONDS_TO_STALE:
            is_stale = True
        return is_stale

    @property
    def percent_played(self) -> int:
        if not self.media_obj:
            return 0

        if self.media_obj and not self.media_obj.run_time_ticks:
            return 100

        if not self.playback_position_ticks and self.played_to_completion:
            return 100

        playback_ticks = self.playback_position_ticks
        if not playback_ticks:
            playback_ticks = (timezone.now() - self.timestamp).seconds * 1000

        percent = int((playback_ticks / self.media_obj.run_time_ticks) * 100)
        if percent > 100:
            percent = 100
        return percent

    @property
    def can_be_updated(self) -> bool:
        updatable = True
        if self.percent_played > 100:
            logger.info(f"No - 100% played - {self.id} - {self.source}")
            updatable = False
        if self.is_stale:
            logger.info(f"No - stale - {self.id} - {self.source}")
            updatable = False
        return updatable

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
        if self.book:
            media_obj = self.book
        return media_obj

    def __str__(self):
        timestamp = self.timestamp.strftime('%Y-%m-%d')
        return f"Scrobble of {self.media_obj} ({timestamp})"

    @classmethod
    def create_or_update(
        cls, media, user_id: int, scrobble_data: dict
    ) -> "Scrobble":

        if media.__class__.__name__ == 'Track':
            media_query = models.Q(track=media)
            scrobble_data['track_id'] = media.id
        if media.__class__.__name__ == 'Video':
            media_query = models.Q(video=media)
            scrobble_data['video_id'] = media.id
        if media.__class__.__name__ == 'Episode':
            media_query = models.Q(podcast_episode=media)
            scrobble_data['podcast_episode_id'] = media.id
        if media.__class__.__name__ == 'SportEvent':
            media_query = models.Q(sport_event=media)
            scrobble_data['sport_event_id'] = media.id
        if media.__class__.__name__ == 'Book':
            media_query = models.Q(book=media)
            scrobble_data['book_id'] = media.id

        scrobble = (
            cls.objects.filter(
                media_query,
                user_id=user_id,
            )
            .order_by('-modified')
            .first()
        )
        if scrobble and scrobble.can_be_updated:
            logger.info(
                f"Updating {scrobble.id}",
                {"scrobble_data": scrobble_data, "media": media},
            )
            return scrobble.update(scrobble_data)

        source = scrobble_data['source']
        logger.info(
            f"Creating for {media.id} - {source}",
            {"scrobble_data": scrobble_data, "media": media},
        )
        # If creating a new scrobble, we don't need status
        scrobble_data.pop('mopidy_status', None)
        scrobble_data.pop('jellyfin_status', None)
        return cls.create(scrobble_data)

    def update(self, scrobble_data: dict) -> "Scrobble":
        # Status is a field we get from Mopidy, which refuses to poll us
        scrobble_status = scrobble_data.pop('mopidy_status', None)
        if not scrobble_status:
            scrobble_status = scrobble_data.pop('jellyfin_status', None)

        if self.percent_played < 100:
            # Only worry about ticks if we haven't gotten to the end
            self.update_ticks(scrobble_data)

        # On stop, stop progress and send it to the check for completion
        if scrobble_status == "stopped":
            self.stop()
        # On pause, set is_paused and stop scrobbling
        if scrobble_status == "paused":
            self.pause()
        if scrobble_status == "resumed":
            self.resume()

        for key, value in scrobble_data.items():
            setattr(self, key, value)
        self.save()
        return self

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
            return
        self.in_progress = False
        self.save(update_fields=['in_progress'])
        logger.info(f"{self.id} - {self.source}")
        check_scrobble_for_finish(self, force_finish)

    def pause(self) -> None:
        if self.is_paused:
            logger.warning(f"{self.id} - already paused - {self.source}")
            return
        self.is_paused = True
        self.save(update_fields=["is_paused"])
        logger.info(f"{self.id} - pausing - {self.source}")
        check_scrobble_for_finish(self)

    def resume(self) -> None:
        if self.is_paused or not self.in_progress:
            self.is_paused = False
            self.in_progress = True
            logger.info(f"{self.id} - resuming - {self.source}")
            return self.save(update_fields=["is_paused", "in_progress"])

    def cancel(self) -> None:
        check_scrobble_for_finish(self, force_finish=True)
        self.delete()

    def update_ticks(self, data) -> None:
        self.playback_position_ticks = data.get("playback_position_ticks")
        self.playback_position = data.get("playback_position")
        logger.info(
            f"{self.id} - {self.playback_position_ticks} - {self.source}"
        )
        self.save(
            update_fields=['playback_position_ticks', 'playback_position']
        )
