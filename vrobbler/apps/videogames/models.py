import logging
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import LongPlayScrobblableMixin
from scrobbles.utils import get_scrobbles_for_media
from videogames.igdb import lookup_game_id_from_gdb

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}
User = get_user_model()


class VideoGamePlatform(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    logo = models.ImageField(upload_to="games/platform-logos/", **BNULL)
    igdb_id = models.IntegerField(**BNULL)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "videogames:platform_detail", kwargs={"slug": self.uuid}
        )


class VideoGameCollection(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    cover = models.ImageField(upload_to="games/series-covers/", **BNULL)
    igdb_id = models.IntegerField(**BNULL)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "videogames:collection_detail", kwargs={"slug": self.uuid}
        )


class VideoGame(LongPlayScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "GAME_COMPLETION_PERCENT", 100)

    FIELDS_FROM_IGDB = [
        "igdb_id",
        "alternative_name",
        "rating",
        "rating_count",
        "release_date",
        "cover",
        "screenshot",
    ]
    FIELDS_FROM_HLTB = [
        "hltb_id",
        "release_year",
        "main_story_time",
        "main_extra_time",
        "completionist_time",
        "hltb_score",
    ]

    title = models.CharField(max_length=255)
    igdb_id = models.IntegerField(**BNULL)
    hltb_id = models.IntegerField(**BNULL)
    alternative_name = models.CharField(max_length=255, **BNULL)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    cover = models.ImageField(upload_to="games/covers/", **BNULL)
    screenshot = models.ImageField(upload_to="games/screenshots/", **BNULL)
    summary = models.TextField(**BNULL)
    hltb_cover = models.ImageField(upload_to="games/hltb_covers/", **BNULL)
    rating = models.FloatField(**BNULL)
    rating_count = models.IntegerField(**BNULL)
    release_date = models.DateTimeField(**BNULL)
    release_year = models.IntegerField(**BNULL)
    main_story_time = models.IntegerField(**BNULL)
    main_extra_time = models.IntegerField(**BNULL)
    completionist_time = models.IntegerField(**BNULL)
    hltb_score = models.FloatField(**BNULL)
    platforms = models.ManyToManyField(VideoGamePlatform)

    def __str__(self):
        return self.title

    @property
    def subtitle(self):
        return f" On {self.platforms.first()}"

    def get_absolute_url(self):
        return reverse(
            "videogames:videogame_detail", kwargs={"slug": self.uuid}
        )

    def hltb_link(self):
        return f"https://howlongtobeat.com/game/{self.hltb_id}"

    def igdb_link(self):
        slug = self.title.lower().replace(" ", "-")
        return f"https://igdb.com/games/{slug}"

    def get_start_url(self):
        return reverse("scrobbles:start", kwargs={"uuid": self.uuid})

    def save(self, **kwargs):
        super().save(**kwargs)
        self.fix_metadata()

    @property
    def seconds_for_completion(self) -> int:
        completion_time = self.run_time_ticks
        if not completion_time:
            # Default to 10 hours, why not
            completion_time = 10 * 60 * 60
        return int(completion_time * (self.COMPLETION_PERCENT / 100))

    def progress_for_user(self, user_id: int) -> int:
        """Used to keep track of whether the game is complete or not"""
        user = User.objects.get(id=user_id)
        last_scrobble = get_scrobbles_for_media(self, user).last()
        if not last_scrobble or not last_scrobble.playback_position:
            logger.warn("No total minutes in last scrobble, no progress")
            return 0
        sec_played = last_scrobble.playback_position * 60
        return int(sec_played / self.run_time) * 100

    def fix_metadata(self, force_update: bool = False):
        from videogames.utils import (
            get_or_create_videogame,
            load_game_data_from_igdb,
        )

        if self.hltb_id and force_update:
            get_or_create_videogame(str(self.hltb_id), force_update)

        if self.igdb_id:
            # This almost never works without intervention
            # self.igdb_id = lookup_game_id_from_gdb(self.title)
            # self.save(update_fields=["igdb_id"])
            load_game_data_from_igdb(self.id)

        if (not self.run_time_ticks or force_update) and self.main_story_time:
            self.run_time_ticks = self.main_story_time * 1000  # miliseconds
            self.run_time = self.main_story_time
            self.save(update_fields=["run_time_ticks", "run_time"])

    @classmethod
    def find_or_create(cls, data_dict: dict) -> "Game":
        from videogames.utils import get_or_create_videogame

        return get_or_create_videogame(data_dict.get("hltb_id"))
