import logging
from typing import Dict, Optional
from uuid import uuid4

import requests
from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from podcasts.scrapers import scrape_data_from_google_podcasts
from scrobbles.mixins import ScrobblableConstants, ScrobblableMixin

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class Producer(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)

    def __str__(self):
        return f"{self.name}"


class Podcast(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    producer = models.ForeignKey(
        Producer, on_delete=models.DO_NOTHING, **BNULL
    )
    description = models.TextField(**BNULL)
    active = models.BooleanField(default=True)
    feed_url = models.URLField(**BNULL)
    google_podcasts_url = models.URLField(**BNULL)
    cover_image = models.ImageField(upload_to="podcasts/covers/", **BNULL)

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("podcasts:podcast_detail", kwargs={"slug": self.uuid})

    def scrobbles(self, user):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(
            user=user, podcast_episode__podcast=self
        ).order_by("-timestamp")

    def scrape_google_podcasts(self, force=False):
        podcast_dict = {}
        if not self.cover_image or force:
            podcast_dict = scrape_data_from_google_podcasts(self.name)
            if podcast_dict:
                if not self.producer:
                    self.producer, created = Producer.objects.get_or_create(
                        name=podcast_dict["producer"]
                    )
                self.description = podcast_dict.get("description")
                self.google_podcasts_url = podcast_dict.get("google_url")
                self.save(
                    update_fields=[
                        "description",
                        "producer",
                        "google_podcasts_url",
                    ]
                )

        cover_url = podcast_dict.get("image_url")
        if (not self.cover_image or force) and cover_url:
            r = requests.get(cover_url)
            if r.status_code == 200:
                fname = f"{self.name}_{self.uuid}.jpg"
                self.cover_image.save(fname, ContentFile(r.content), save=True)


class PodcastEpisode(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "PODCAST_COMPLETION_PERCENT", 90)

    podcast = models.ForeignKey(Podcast, on_delete=models.DO_NOTHING)
    number = models.IntegerField(**BNULL)
    pub_date = models.DateField(**BNULL)
    mopidy_uri = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return f"{self.title}"

    @property
    def subtitle(self):
        return self.podcast

    @property
    def strings(self) -> ScrobblableConstants:
        return ScrobblableConstants(verb="Listening", tags="microphone")

    @property
    def info_link(self):
        return ""

    @property
    def primary_image_url(self) -> str:
        url = ""
        if self.podcast.cover_image:
            url = self.podcast.cover_image.url
        return url

    @classmethod
    def find_or_create(
        cls, podcast_dict: Dict, producer_dict: Dict, episode_dict: Dict
    ) -> Optional["Episode"]:
        """Given a data dict from Mopidy, finds or creates a podcast and
        producer before saving the epsiode so it can be scrobbled.

        """
        if not podcast_dict.get("name"):
            logger.warning(f"No name from source for podcast, not scrobbling")
            return

        producer = None
        if producer_dict.get("name"):
            producer, producer_created = Producer.objects.get_or_create(
                **producer_dict
            )
            if producer_created:
                logger.debug(f"Created new producer {producer}")
            else:
                logger.debug(f"Found producer {producer}")

        if producer:
            podcast_dict["producer_id"] = producer.id
        podcast, podcast_created = Podcast.objects.get_or_create(
            **podcast_dict
        )
        if podcast_created:
            logger.debug(f"Created new podcast {podcast}")
        else:
            logger.debug(f"Found podcast {podcast}")

        episode_dict["podcast_id"] = podcast.id

        episode, created = cls.objects.get_or_create(**episode_dict)
        if created:
            logger.debug(f"Created new episode: {episode}")
        else:
            logger.debug(f"Found episode {episode}")

        return episode
