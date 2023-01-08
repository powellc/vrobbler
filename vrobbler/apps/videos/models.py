import logging
from typing import Dict, Tuple
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Series(TimeStampedModel):
    name = models.CharField(max_length=255)
    overview = models.TextField(**BNULL)
    tagline = models.TextField(**BNULL)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "series"


class Video(TimeStampedModel):
    class VideoType(models.TextChoices):
        UNKNOWN = 'U', _('Unknown')
        TV_EPISODE = 'E', _('TV Episode')
        MOVIE = 'M', _('Movie')

    # General fields
    video_type = models.CharField(
        max_length=1,
        choices=VideoType.choices,
        default=VideoType.UNKNOWN,
    )
    title = models.CharField(max_length=255, **BNULL)
    overview = models.TextField(**BNULL)
    tagline = models.TextField(**BNULL)
    run_time = models.CharField(max_length=8, **BNULL)
    run_time_ticks = models.PositiveBigIntegerField(**BNULL)
    year = models.IntegerField()

    # TV show specific fields
    tv_series = models.ForeignKey(Series, on_delete=models.DO_NOTHING, **BNULL)
    season_number = models.IntegerField(**BNULL)
    episode_number = models.IntegerField(**BNULL)
    tvdb_id = models.CharField(max_length=20, **BNULL)
    imdb_id = models.CharField(max_length=20, **BNULL)
    tvrage_id = models.CharField(max_length=20, **BNULL)

    # Metadata fields from TMDB

    def __str__(self):
        if self.video_type == self.VideoType.TV_EPISODE:
            return f"{self.tv_series} - Season {self.season_number}, Episode {self.episode_number}"
        return self.title


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
            "year": data_dict.get("Year", ""),
            "overview": data_dict.get("Overview", None),
            "tagline": data_dict.get("Tagline", None),
            "run_time_ticks": data_dict.get("RunTimeTicks", None),
            "run_time": data_dict.get("RunTime", None),
        }

        if data_dict.get("ItemType", "") == "Episode":
            series_name = data_dict.get("SeriesName", "")
            series, series_created = Series.objects.get_or_create(name=series_name)
            if series_created:
                logger.debug(f"Created new series {series}")
            else:
                logger.debug(f"Found series {series}")
            video_dict['video_type'] = Video.VideoType.TV_EPISODE
            video_dict["tv_series_id"] = series.id
            video_dict["tvdb_id"] = data_dict.get("Provider_tvdb", None)
            video_dict["tvrage_id"] = data_dict.get("Provider_tvrage", None)
            video_dict["episode_number"] = data_dict.get("EpisodeNumber", "")
            video_dict["season_number"] = data_dict.get("SeasonNumber", "")


        video, created = cls.objects.get_or_create(**video_dict)
        if created:
            logger.debug(f"Created new video: {video}")
        else:
            logger.debug(f"Found video {video}")

        return video
