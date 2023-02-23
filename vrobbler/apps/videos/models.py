import logging
from typing import Dict
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from scrobbles.utils import convert_to_seconds
from scrobbles.mixins import ScrobblableMixin

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Series(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    name = models.CharField(max_length=255)
    overview = models.TextField(**BNULL)
    tagline = models.TextField(**BNULL)
    # tvdb_id = models.CharField(max_length=20, **BNULL)
    # imdb_id = models.CharField(max_length=20, **BNULL)

    def __str__(self):
        return self.name

    def imdb_link(self):
        return f"https://www.imdb.com/title/{self.imdb_id}"

    class Meta:
        verbose_name_plural = "series"


class Video(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, 'VIDEO_COMPLETION_PERCENT', 90)
    SECONDS_TO_STALE = getattr(settings, 'VIDEO_SECONDS_TO_STALE', 14400)

    class VideoType(models.TextChoices):
        UNKNOWN = 'U', _('Unknown')
        TV_EPISODE = 'E', _('TV Episode')
        MOVIE = 'M', _('Movie')

    video_type = models.CharField(
        max_length=1,
        choices=VideoType.choices,
        default=VideoType.UNKNOWN,
    )
    overview = models.TextField(**BNULL)
    tagline = models.TextField(**BNULL)
    year = models.IntegerField(**BNULL)

    # TV show specific fields
    tv_series = models.ForeignKey(Series, on_delete=models.DO_NOTHING, **BNULL)
    season_number = models.IntegerField(**BNULL)
    episode_number = models.IntegerField(**BNULL)
    tvdb_id = models.CharField(max_length=20, **BNULL)
    imdb_id = models.CharField(max_length=20, **BNULL)
    tvrage_id = models.CharField(max_length=20, **BNULL)

    class Meta:
        unique_together = [['title', 'imdb_id']]

    def __str__(self):
        if self.video_type == self.VideoType.TV_EPISODE:
            return f"{self.tv_series} - Season {self.season_number}, Episode {self.episode_number}"
        return self.title

    def get_absolute_url(self):
        return reverse("videos:video_detail", kwargs={'slug': self.uuid})

    @property
    def subtitle(self):
        if self.tv_series:
            return self.tv_series
        return ""

    @property
    def imdb_link(self):
        return f"https://www.imdb.com/title/{self.imdb_id}"

    @property
    def info_link(self):
        return self.imdb_link

    @property
    def link(self):
        return self.imdb_link

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> "Video":
        """Given a data dict from Jellyfin, does the heavy lifting of looking up
        the video and, if need, TV Series, creating both if they don't yet
        exist.

        """
        video_dict = {
            "title": data_dict.get("Name", ""),
            "imdb_id": data_dict.get("Provider_imdb", None),
            "video_type": Video.VideoType.MOVIE,
        }

        series = None
        if data_dict.get("ItemType", "") == "Episode":
            series_name = data_dict.get("SeriesName", "")
            series, series_created = Series.objects.get_or_create(
                name=series_name
            )
            video_dict['video_type'] = Video.VideoType.TV_EPISODE

        video, created = cls.objects.get_or_create(**video_dict)

        run_time_ticks = data_dict.get("RunTimeTicks", None)
        if run_time_ticks:
            run_time_ticks = run_time_ticks // 10000

        video_extra_dict = {
            "year": data_dict.get("Year", ""),
            "overview": data_dict.get("Overview", None),
            "tagline": data_dict.get("Tagline", None),
            "run_time_ticks": run_time_ticks,
            "run_time": convert_to_seconds(data_dict.get("RunTime", "")),
            "tvdb_id": data_dict.get("Provider_tvdb", None),
            "tvrage_id": data_dict.get("Provider_tvrage", None),
            "episode_number": data_dict.get("EpisodeNumber", None),
            "season_number": data_dict.get("SeasonNumber", None),
        }

        if series:
            video_extra_dict["tv_series_id"] = series.id

        if not video.run_time_ticks:
            for key, value in video_extra_dict.items():
                setattr(video, key, value)
            video.save()

        return video
