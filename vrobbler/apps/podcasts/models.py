import logging
from typing import Dict, Optional
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from scrobbles.mixins import ScrobblableMixin

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
    active = models.BooleanField(default=True)
    url = models.URLField(**BNULL)

    def __str__(self):
        return f"{self.name}"


class Episode(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, 'PODCAST_COMPLETION_PERCENT', 90)

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
    def info_link(self):
        return ""

    @classmethod
    def find_or_create(
        cls, podcast_dict: Dict, producer_dict: Dict, episode_dict: Dict
    ) -> Optional["Episode"]:
        """Given a data dict from Mopidy, finds or creates a podcast and
        producer before saving the epsiode so it can be scrobbled.

        """
        if not podcast_dict.get('name'):
            logger.warning(f"No name from source for podcast, not scrobbling")
            return

        producer = None
        if producer_dict.get('name'):
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

        episode_dict['podcast_id'] = podcast.id

        episode, created = cls.objects.get_or_create(**episode_dict)
        if created:
            logger.debug(f"Created new episode: {episode}")
        else:
            logger.debug(f"Found episode {episode}")

        return episode
