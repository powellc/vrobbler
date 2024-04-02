import logging
from typing import Dict
from uuid import uuid4
from django_extensions.db.models import TimeStampedModel

import pendulum
import requests
from taggit.managers import TaggableManager
import trafilatura
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from htmldate import find_date
from scrobbles.mixins import ScrobblableMixin

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}
User = get_user_model()


class Domain(TimeStampedModel):
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    root = models.CharField(max_length=255)
    name = models.CharField(max_length=255, **BNULL)

    tags = TaggableManager(blank=True)

    def __str__(self):
        if self.name:
            return self.name
        return self.root

    def scrobbles_for_user(self, user_id):
        from scrobbles.models import Scrobble

        return Scrobble.objects.filter(
            web_page__domain=self, user_id=user_id
        ).order_by("-timestamp")


class WebPage(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "WEBSITE_COMPLETION_PERCENT", 100)

    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    url = models.URLField(max_length=500)
    date = models.DateField(**BNULL)
    domain = models.ForeignKey(Domain, on_delete=models.DO_NOTHING, **BNULL)
    extract = models.TextField(**BNULL)

    def __str__(self):
        if self.title:
            return self.title
        if self.domain:
            return self.domain
        return str(self.uuid)

    def _raw_domain(self):
        self.url.split("//")[-1].split("/")[0]

    def _update_extract_from_web(self, force=True):
        headers = {
            "headers": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0"
        }
        raw_text = requests.get(self.url, headers=headers).text
        if not self.extract or force:
            self.extract = trafilatura.extract(raw_text)
            self.save(update_fields=["extract"])

    def get_absolute_url(self):
        return reverse("webpages:webpage_detail", kwargs={"slug": self.uuid})

    @property
    def estimated_time_to_read_in_seconds(self):
        if not self.extract:
            return 600

        words_per_minute = getattr(settings, "READING_WORDS_PER_MINUTE", 200)
        words = len(self.extract.split(" "))
        return int(words / words_per_minute) * 60

    @property
    def estimated_time_to_read_in_minutes(self):
        return int(self.estimated_time_to_read_in_seconds / 60)

    @property
    def subtitle(self):
        return self.domain

    def scrobbles(self, user):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(user=user, web_page=self).order_by(
            "-timestamp"
        )

    def clean_title(self, title: str, save=True):
        if len(title.split('|')) > 1:
            if "The Quietus" in title:
                title = title.split('|')[-0]
            else:
                title = title.split('|')[0]
        if len(title.split('&#8211;')) > 1:
            title = title.split('&#8211;')[0]
        if len(title.split(' - ')) > 1:
            title = title.split(' - ')[0]
        self.title = title.strip()
        if save:
            self.save(update_fields=["title"])



    def _update_domain_from_url(self):
        domain = self.url.split("//")[-1].split("/")[0].split("www.")[-1]
        self.domain, created = Domain.objects.get_or_create(root=domain)

    def _update_data_from_web(self, force=True):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0"
        }
        raw_text = requests.get(self.url, headers=headers).text
        if not self.title or force:
            self.set_title(raw_text[
                raw_text.find("<title>") + 7 : raw_text.find("</title>")
            ])
        try:
            date_str = find_date(str(self.url))
        except ValueError:
            date_str = ""
        if date_str:
            self.date = pendulum.parse(date_str).date()

        if not self.extract or force:
            self.extract = trafilatura.extract(raw_text)
            if not self.title:
                first_line = self.extract.split("\n")[0]
                if len(first_line) < 254:
                    self.title = first_line

        if not self.domain or force:
            self._update_domain_from_url()

        if not self.run_time_seconds or force:
            self.run_time_seconds = self.estimated_time_to_read_in_seconds

        self.save(
            update_fields=[
                "title",
                "domain",
                "extract",
                "run_time_seconds",
                "date",
            ]
        )

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> "GeoLocation":
        """Given a data dict from an manual URL scrobble, does the heavy lifting of looking up
        the url, creating if if doesn't exist yet.

        """
        # TODO Add constants for all these data keys
        if "url" not in data_dict.keys():
            logger.error("No url in data dict")
            return

        webpage = cls.objects.filter(url=data_dict.get("url")).first()

        if not webpage:
            webpage = cls.objects.create(url=data_dict.get("url"))
            webpage._update_data_from_web()
        return webpage
