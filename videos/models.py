from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _

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
    run_time_ticks = models.BigIntegerField(**BNULL)
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
