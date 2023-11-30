import requests
import logging
from typing import Dict
import trafilatura
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models
from django.urls import reverse
from scrobbles.mixins import ScrobblableMixin

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}
User = get_user_model()


class WebPage(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "WEBSITE_COMPLETION_PERCENT", 100)

    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    url = models.URLField(max_length=500)
    domain = models.CharField(max_length=200, **BNULL)
    extract = models.TextField(**BNULL)

    def __str__(self):
        if self.title:
            return self.title

        return self.domain

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

    def _update_data_from_web(self, force=True):
        headers = {
            "headers": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0"
        }
        raw_text = requests.get(self.url, headers=headers).text
        if not self.title or force:
            self.title = raw_text[
                raw_text.find("<title>") + 7 : raw_text.find("</title>")
            ]

        if not self.extract or force:
            self.extract = trafilatura.extract(raw_text)

        if not self.domain or force:
            self.domain = self.url.split("//")[-1].split("/")[0]

        self.save(update_fields=["title", "domain", "extract"])

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
            webpage.run_time_seconds = settings.get("WEBSITE_READ_TIME", 600)
            webpage._update_data_from_web()
        return webpage
