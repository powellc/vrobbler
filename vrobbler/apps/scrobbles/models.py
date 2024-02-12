import calendar
import datetime
from decimal import Decimal
import logging
from typing import Optional
from uuid import uuid4

from boardgames.models import BoardGame
from books.koreader import process_koreader_sqlite_file
from books.models import Book
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django_extensions.db.models import TimeStampedModel
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from locations.models import GeoLocation
from music.lastfm import LastFM
from music.models import Artist, Track
from podcasts.models import PodcastEpisode
from profiles.utils import (
    end_of_day,
    end_of_month,
    end_of_week,
    start_of_day,
    start_of_month,
    start_of_week,
)
from scrobbles.constants import LONG_PLAY_MEDIA
from scrobbles.stats import build_charts
from scrobbles.utils import (
    check_long_play_for_finish,
    check_scrobble_for_finish,
    media_class_to_foreign_key,
)
from sports.models import SportEvent
from videogames import retroarch
from videogames.models import VideoGame
from videos.models import Series, Video
from webpages.models import WebPage

logger = logging.getLogger(__name__)
User = get_user_model()
BNULL = {"blank": True, "null": True}

POINTS_FOR_MOVEMENT_HISTORY = int(
    getattr(settings, "POINTS_FOR_MOVEMENT_HISTORY", 3)
)


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
        return f"{self.import_type} import on {self.human_start}"

    @property
    def human_start(self):
        start = "Unknown"
        if self.processing_started:
            start = self.processing_started.strftime("%B %d, %Y at %H:%M")
        return start

    @property
    def import_type(self) -> str:
        return "Unknown Import Source"

    def process(self, force=False):
        logger.warning("Process not implemented")

    def undo(self, dryrun=False):
        """Accepts the log from a scrobble import and removes the scrobbles"""
        from scrobbles.models import Scrobble

        if not self.process_log:

            logger.warning("No lines in process log found to undo")
            return

        for line in self.process_log.split("\n"):
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

    def scrobbles(self) -> models.QuerySet:
        scrobble_ids = []
        if self.process_log:
            for line in self.process_log.split("\n"):
                sid = line.split("\t")[0]
                if sid:
                    scrobble_ids.append(sid)
        return Scrobble.objects.filter(id__in=scrobble_ids)

    def mark_started(self):
        self.processing_started = timezone.now()
        self.save(update_fields=["processing_started"])

    def mark_finished(self):
        self.processed_finished = timezone.now()
        self.save(update_fields=["processed_finished"])

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

    @property
    def upload_file_path(self):
        raise NotImplementedError


class KoReaderImport(BaseFileImportMixin):
    class Meta:
        verbose_name = "KOReader Import"

    @property
    def import_type(self) -> str:
        return "KOReader"

    def get_absolute_url(self):
        return reverse(
            "scrobbles:koreader-import-detail", kwargs={"slug": self.uuid}
        )

    def get_path(instance, filename):
        extension = filename.split(".")[-1]
        uuid = instance.uuid
        return f"koreader-uploads/{uuid}.{extension}"

    @property
    def upload_file_path(self) -> str:
        if getattr(settings, "USE_S3_STORAGE"):
            path = self.sqlite_file.url
        else:
            path = self.sqlite_file.path
        return path

    sqlite_file = models.FileField(upload_to=get_path, **BNULL)

    def process(self, force=False):

        if self.processed_finished and not force:
            logger.info(
                f"{self} already processed on {self.processed_finished}"
            )
            return

        self.mark_started()
        scrobbles = process_koreader_sqlite_file(
            self.upload_file_path, self.user.id
        )
        self.record_log(scrobbles)
        self.mark_finished()


class AudioScrobblerTSVImport(BaseFileImportMixin):
    class Meta:
        verbose_name = "AudioScrobbler TSV Import"

    @property
    def import_type(self) -> str:
        return "AudiosScrobbler"

    def get_absolute_url(self):
        return reverse(
            "scrobbles:tsv-import-detail", kwargs={"slug": self.uuid}
        )

    def get_path(instance, filename):
        extension = filename.split(".")[-1]
        uuid = instance.uuid
        return f"audioscrobbler-uploads/{uuid}.{extension}"

    @property
    def upload_file_path(self):
        if getattr(settings, "USE_S3_STORAGE"):
            path = self.tsv_file.url
        else:
            path = self.tsv_file.path
        return path

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
        user_id = None
        if self.user:
            user_id = self.user.id
            tz = self.user.profile.tzinfo
        scrobbles = process_audioscrobbler_tsv_file(
            self.upload_file_path, user_id, user_tz=tz
        )
        self.record_log(scrobbles)
        self.mark_finished()


class LastFmImport(BaseFileImportMixin):
    class Meta:
        verbose_name = "Last.FM Import"

    @property
    def import_type(self) -> str:
        return "LastFM"

    def get_absolute_url(self):
        return reverse(
            "scrobbles:lastfm-import-detail", kwargs={"slug": self.uuid}
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


class RetroarchImport(BaseFileImportMixin):
    class Meta:
        verbose_name = "Retroarch Import"

    @property
    def import_type(self) -> str:
        return "Retroarch"

    def get_absolute_url(self):
        return reverse(
            "scrobbles:retroarch-import-detail", kwargs={"slug": self.uuid}
        )

    def process(self, import_all=False, force=False):
        """Import scrobbles found on Retroarch"""
        if self.processed_finished and not force:
            logger.info(
                f"{self} already processed on {self.processed_finished}"
            )
            return

        if force:
            logger.info(f"You told me to force import from Retroarch")

        if not self.user.profile.retroarch_path:
            logger.info(
                "Tying to import Retroarch logs, but user has no retroarch_path configured"
            )

        self.mark_started()

        scrobbles = retroarch.import_retroarch_lrtl_files(
            self.user.profile.retroarch_path,
            self.user.id,
        )

        self.record_log(scrobbles)
        self.mark_finished()


class ChartRecord(TimeStampedModel):
    """Sort of like a materialized view for what we could dynamically generate,
    but would kill the DB as it gets larger. Collects time-based records
    generated by a cron-like archival job

    1972 by Josh Rouse - #3 in 2023, January

    """

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, **BNULL)
    rank = models.IntegerField(db_index=True)
    count = models.IntegerField(default=0)
    year = models.IntegerField(**BNULL)
    month = models.IntegerField(**BNULL)
    week = models.IntegerField(**BNULL)
    day = models.IntegerField(**BNULL)
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, **BNULL)
    series = models.ForeignKey(Series, on_delete=models.DO_NOTHING, **BNULL)
    artist = models.ForeignKey(Artist, on_delete=models.DO_NOTHING, **BNULL)
    track = models.ForeignKey(Track, on_delete=models.DO_NOTHING, **BNULL)
    period_start = models.DateTimeField(**BNULL)
    period_end = models.DateTimeField(**BNULL)

    def save(self, *args, **kwargs):
        profile = self.user.profile

        if self.week:
            # set start and end to start and end of week
            period = datetime.date.fromisocalendar(self.year, self.week, 1)
            self.period_start = start_of_week(period, profile)
            self.period_start = end_of_week(period, profile)
        if self.day:
            period = datetime.datetime(self.year, self.month, self.day)
            self.period_start = start_of_day(period, profile)
            self.period_end = end_of_day(period, profile)
        if self.month and not self.day:
            period = datetime.datetime(self.year, self.month, 1)
            self.period_start = start_of_month(period, profile)
            self.period_end = end_of_month(period, profile)
        super(ChartRecord, self).save(*args, **kwargs)

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
        period = "year"
        if self.month:
            period = "month"
        if self.week:
            period = "week"
        if self.day:
            period = "day"
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
        return reverse("scrobbles:charts-home") + get_params

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

    class MediaType(models.TextChoices):
        """Enum mapping a media model type to a string"""

        VIDEO = "Video", "Video"
        TRACK = "Track", "Track"
        PODCAST_EPISODE = "PodcastEpisode", "Podcast episode"
        SPORT_EVENT = "SportEvent", "Sport event"
        BOOK = "Book", "Book"
        VIDEO_GAME = "VideoGame", "Video game"
        BOARD_GAME = "BoardGame", "Board game"
        GEO_LOCATION = "GeoLocation", "GeoLocation"
        WEBPAGE = "WebPage", "Web Page"

    uuid = models.UUIDField(editable=False, **BNULL)
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, **BNULL)
    track = models.ForeignKey(Track, on_delete=models.DO_NOTHING, **BNULL)
    podcast_episode = models.ForeignKey(
        PodcastEpisode, on_delete=models.DO_NOTHING, **BNULL
    )
    sport_event = models.ForeignKey(
        SportEvent, on_delete=models.DO_NOTHING, **BNULL
    )
    book = models.ForeignKey(Book, on_delete=models.DO_NOTHING, **BNULL)
    video_game = models.ForeignKey(
        VideoGame, on_delete=models.DO_NOTHING, **BNULL
    )
    board_game = models.ForeignKey(
        BoardGame, on_delete=models.DO_NOTHING, **BNULL
    )
    geo_location = models.ForeignKey(
        GeoLocation, on_delete=models.DO_NOTHING, **BNULL
    )
    webpage = models.ForeignKey(WebPage, on_delete=models.DO_NOTHING, **BNULL)
    media_type = models.CharField(
        max_length=14, choices=MediaType.choices, default=MediaType.VIDEO
    )
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.DO_NOTHING
    )

    # Time keeping
    timestamp = models.DateTimeField(**BNULL)
    stop_timestamp = models.DateTimeField(**BNULL)
    playback_position_ticks = models.PositiveBigIntegerField(**BNULL)
    playback_position_seconds = models.IntegerField(**BNULL)

    # Status indicators
    is_paused = models.BooleanField(default=False)
    played_to_completion = models.BooleanField(default=False)
    in_progress = models.BooleanField(default=True)

    # Metadata
    source = models.CharField(max_length=255, **BNULL)
    source_id = models.TextField(**BNULL)
    scrobble_log = models.TextField(**BNULL)
    notes = models.TextField(**BNULL)

    # Fields for keeping track of book data
    book_koreader_hash = models.CharField(max_length=50, **BNULL)
    book_pages_read = models.IntegerField(**BNULL)
    book_page_data = models.JSONField(**BNULL)

    # Fields for keeping track of video game data
    videogame_save_data = models.FileField(
        upload_to="scrobbles/videogame_save_data/", **BNULL
    )
    videogame_screenshot = models.ImageField(
        upload_to="scrobbles/videogame_screenshot/", **BNULL
    )
    videogame_screenshot_small = ImageSpecField(
        source="videogame_screenshot",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    videogame_screenshot_medium = ImageSpecField(
        source="videogame_screenshot",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    long_play_seconds = models.BigIntegerField(**BNULL)
    long_play_complete = models.BooleanField(**BNULL)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = uuid4()

        # Microseconds mess up Django's filtering, and we don't need be that specific
        if self.timestamp:
            self.timestamp = self.timestamp.replace(microsecond=0)
        self.media_type = self.MediaType(self.media_obj.__class__.__name__)

        return super(Scrobble, self).save(*args, **kwargs)

    @property
    def scrobble_media_key(self) -> str:
        return media_class_to_foreign_key(self.media_type) + "_id"

    @property
    def status(self) -> str:
        if self.is_paused:
            return "paused"
        if self.played_to_completion:
            return "finished"
        if self.in_progress:
            return "in-progress"
        return "zombie"

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
    def previous(self) -> "Scrobble":
        return (
            self.media_obj.scrobble_set.order_by("-timestamp")
            .filter(timestamp__lt=self.timestamp)
            .first()
        )

    @property
    def next(self) -> "Scrobble":
        return (
            self.media_obj.scrobble_set.order_by("timestamp")
            .filter(timestamp__gt=self.timestamp)
            .first()
        )

    @property
    def previous_by_media(self) -> "Scrobble":
        return (
            Scrobble.objects.filter(
                media_type=self.media_type,
                user=self.user,
                timestamp__lt=self.timestamp,
            )
            .order_by("-timestamp")
            .first()
        )

    @property
    def next_by_media(self) -> "Scrobble":
        return (
            Scrobble.objects.filter(
                media_type=self.media_type,
                user=self.user,
                timestamp__gt=self.timestamp,
            )
            .order_by("-timestamp")
            .first()
        )

    @property
    def previous_by_user(self) -> "Scrobble":
        return (
            Scrobble.objects.order_by("-timestamp")
            .filter(timestamp__lt=self.timestamp)
            .first()
        )

    @property
    def next_by_user(self) -> "Scrobble":
        return (
            Scrobble.objects.order_by("-timestamp")
            .filter(timestamp__gt=self.timestamp)
            .first()
        )

    @property
    def session_pages_read(self) -> Optional[int]:
        """Look one scrobble back, if it isn't complete,"""
        if not self.book_pages_read:
            return
        if self.previous:
            return self.book_pages_read - self.previous.book_pages_read
        return self.book_pages_read

    @property
    def is_long_play(self) -> bool:
        return self.media_obj.__class__.__name__ in LONG_PLAY_MEDIA.values()

    @property
    def percent_played(self) -> int:
        if not self.media_obj:
            return 0

        if self.media_obj and not self.media_obj.run_time_seconds:
            return 100

        if not self.playback_position_seconds and self.played_to_completion:
            return 100

        playback_seconds = self.playback_position_seconds
        if not playback_seconds:
            playback_seconds = (timezone.now() - self.timestamp).seconds

        run_time_secs = self.media_obj.run_time_seconds
        percent = int((playback_seconds / run_time_secs) * 100)

        if self.is_long_play:
            long_play_secs = 0
            if self.previous and not self.previous.long_play_complete:
                long_play_secs = self.previous.long_play_seconds or 0
            percent = int(
                ((playback_seconds + long_play_secs) / run_time_secs) * 100
            )

        # if percent > 100:
        #    percent = 100

        return percent

    @property
    def can_be_updated(self) -> bool:
        updatable = True

        if self.media_obj.__class__.__name__ in LONG_PLAY_MEDIA.values():
            logger.info(f"No - Long play media")
            updatable = False
        if self.percent_played >= 100:
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
        if self.video_game:
            media_obj = self.video_game
        if self.board_game:
            media_obj = self.board_game
        if self.geo_location:
            media_obj = self.geo_location
        if self.webpage:
            media_obj = self.webpage
        return media_obj

    def __str__(self):
        timestamp = self.timestamp.strftime("%Y-%m-%d")
        return f"Scrobble of {self.media_obj} ({timestamp})"

    def calc_reading_duration(self) -> int:
        duration = 0
        if self.book_page_data:
            for k, v in self.book_page_data.items():
                duration += v.get("duration")
        return duration

    def calc_pages_read(self) -> int:
        pages_read = 0
        if self.book_page_data:
            pages = [int(k) for k in self.book_page_data.keys()]
            pages.sort()
            pages_read = pages[-1] - pages[0]
        return pages_read

    @classmethod
    def create_or_update(
        cls, media, user_id: int, scrobble_data: dict, **kwargs
    ) -> "Scrobble":
        key = media_class_to_foreign_key(media.__class__.__name__)
        media_query = models.Q(**{key: media})
        scrobble_data[key + "_id"] = media.id

        # Find our last scrobble of this media item (track, video, etc)
        scrobble = (
            cls.objects.filter(
                media_query,
                user_id=user_id,
            )
            .order_by("-timestamp")
            .first()
        )
        source = scrobble_data["source"]
        mtype = media.__class__.__name__

        # Do some funny stuff if it's a geo location
        if mtype == cls.MediaType.GEO_LOCATION:
            moved_location = cls.user_has_moved_locations(media, user_id)
            if not moved_location:
                logger.info(
                    f"[scrobbling] updating {scrobble.id} for {mtype} {media.id} from {source}",
                    {"scrobble_data": scrobble_data, "media": media},
                )
                scrobble.update(scrobble_data)
            else:
                logger.info(
                    f"[scrobbling] finishing {scrobble.id} for {mtype} {media.id} from {source}",
                    {"scrobble_data": scrobble_data, "media": media},
                )
                scrobble.stop()
                # Just blank our scrobble so we create a new one
                scrobble = None

        if scrobble and scrobble.can_be_updated:
            logger.info(
                f"[scrobbling] updating {scrobble.id} for {mtype} {media.id} from {source}",
                {"scrobble_data": scrobble_data, "media": media},
            )
            return scrobble.update(scrobble_data)

        # Discard status before creating
        scrobble_data.pop("mopidy_status", None)
        scrobble_data.pop("jellyfin_status", None)
        logger.info(
            f"[scrobbling] creating for {mtype} {media.id} from {source}"
        )
        return cls.create(scrobble_data)

    @classmethod
    def user_has_moved_locations(
        cls, location: GeoLocation, user_id: int
    ) -> bool:
        moved_location = False
        scrobble = (
            cls.objects.filter(
                media_type=cls.MediaType.GEO_LOCATION, user_id=user_id
            )
            .order_by("-timestamp")
            .first()
        )
        if not scrobble:
            logger.info(
                f"[scrobbling] No existing location scrobbles, {location} should be created"
            )
            moved_location = True

        else:
            if scrobble.media_obj == location:
                logger.info(
                    f"[scrobbling] New location {location} and last location {scrobble.media_obj} are the same"
                )
                moved_location = False

            if scrobble.media_obj != location:
                logger.info(
                    f"[scrobbling] New location {location} and last location {scrobble.media_obj} are different"
                )
                past_scrobbles = Scrobble.objects.filter(
                    media_type="GeoLocation",
                    user_id=user_id,
                ).order_by("-timestamp")[1:POINTS_FOR_MOVEMENT_HISTORY]
                past_points = [s.media_obj for s in past_scrobbles]

                moved_location = location.has_moved(past_points)
        return moved_location

    def update(self, scrobble_data: dict) -> "Scrobble":
        # Status is a field we get from Mopidy, which refuses to poll us
        scrobble_status = scrobble_data.pop("mopidy_status", None)
        if not scrobble_status:
            scrobble_status = scrobble_data.pop("jellyfin_status", None)

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

        check_scrobble_for_finish(self)

        if scrobble_status != "resumed":
            scrobble_data["stop_timestamp"] = (
                scrobble_data.pop("timestamp", None) or timezone.now()
            )

        scrobble_data.pop("timestamp", None)
        update_fields = []
        for key, value in scrobble_data.items():
            setattr(self, key, value)
            update_fields.append(key)
        self.save(update_fields=update_fields)

        return self

    @classmethod
    def create(
        cls,
        scrobble_data: dict,
    ) -> "Scrobble":
        scrobble_data["scrobble_log"] = ""
        scrobble = cls.objects.create(
            **scrobble_data,
        )
        return scrobble

    def stop(self, force_finish=False) -> None:
        self.stop_timestamp = timezone.now()
        if force_finish:
            self.played_to_completion = True
        self.in_progress = False
        if not self.playback_position_seconds:
            self.playback_position_seconds = int(
                (self.stop_timestamp - self.timestamp).total_seconds()
            )

        self.save(
            update_fields=[
                "in_progress",
                "played_to_completion",
                "stop_timestamp",
                "playback_position_seconds",
            ]
        )
        logger.info(f"stopping {self.id} from {self.source}")

        class_name = self.media_obj.__class__.__name__
        if class_name in LONG_PLAY_MEDIA.values():
            check_long_play_for_finish(self)

    def pause(self) -> None:
        if self.is_paused:
            logger.warning(f"{self.id} - already paused - {self.source}")
            return
        logger.info(f"{self.id} - pausing - {self.source}")
        self.is_paused = True
        self.save(update_fields=["is_paused"])

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
        self.playback_position_seconds = data.get("playback_position_seconds")
        logger.info(
            f"{self.id} - {self.playback_position_seconds} - {self.source}"
        )
        self.save(update_fields=["playback_position_seconds"])


class ScrobbledPage(TimeStampedModel):
    scrobble = models.ForeignKey(Scrobble, on_delete=models.DO_NOTHING)
    number = models.IntegerField()
    start_time = models.DateTimeField(**BNULL)
    end_time = models.DateTimeField(**BNULL)
    duration_seconds = models.IntegerField(**BNULL)
    notes = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return f"Page {self.number} of {self.book.pages} in {self.book.title}"

    def save(self, *args, **kwargs):
        if not self.end_time and self.duration_seconds:
            self._set_end_time()

        return super(ScrobbledPage, self).save(*args, **kwargs)

    @cached_property
    def book(self):
        return self.scrobble.book

    @property
    def next(self):
        user_pages_qs = self.book.scrobbledpage_set.filter(
            user=self.scrobble.user
        )
        page = user_pages_qs.filter(number=self.number + 1).first()
        if not page:
            page = (
                user_pages_qs.filter(created__gt=self.created)
                .order_by("created")
                .first()
            )
        return page

    @property
    def previous(self):
        user_pages_qs = self.book.scrobbledpage_set.filter(
            user=self.scrobble.user
        )
        page = user_pages_qs.filter(number=self.number - 1).first()
        if not page:
            page = (
                user_pages_qs.filter(created__lt=self.created)
                .order_by("-created")
                .first()
            )
        return page

    @property
    def seconds_to_next_page(self) -> int:
        seconds = 999999  # Effectively infnity time as we have no next
        if not self.end_time:
            self._set_end_time()
        if self.next:
            seconds = (self.next.start_time - self.end_time).seconds
        return seconds

    @property
    def is_scrobblable(self) -> bool:
        """A page defines the start of a scrobble if the seconds to next page
        are greater than an hour, or 3600 seconds, and it's not a single page,
        so the next seconds to next_page is less than an hour as well.

        As a special case, the first recorded page is a scrobble, so we establish
        when the book was started.

        """
        is_scrobblable = False
        over_an_hour_since_last_page = False
        if not self.previous:
            is_scrobblable = True

        if self.previous:
            over_an_hour_since_last_page = (
                self.previous.seconds_to_next_page >= 3600
            )
        blip = self.seconds_to_next_page >= 3600

        if over_an_hour_since_last_page and not blip:
            is_scrobblable = True
        return is_scrobblable

    def _set_end_time(self) -> None:
        if self.end_time:
            return

        self.end_time = self.start_time + datetime.timedelta(
            seconds=self.duration_seconds
        )
        self.save(update_fields=["end_time"])
