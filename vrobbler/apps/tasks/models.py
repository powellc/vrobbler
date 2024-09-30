from dataclasses import dataclass
from enum import Enum
from typing import Optional

from django.apps import apps
from django.db import models
from django.urls import reverse
from scrobbles.dataclasses import LongPlayLogData
from scrobbles.mixins import LongPlayScrobblableMixin

BNULL = {"blank": True, "null": True}

TASK_SOURCE_URL_PATTERNS = [
    ("https://app.shortcut.com/sure/story/{id}", "Shortcut"),
    ("https://app.todoist.com/app/task/{id}", "Todoist"),
]


@dataclass
class TaskLogData(LongPlayLogData):
    source_id: Optional[str] = None
    serial_scrobble_id: Optional[int] = None
    long_play_complete: Optional[bool] = None


class TaskType(Enum):
    PRO = "Professional"
    AMATEUR = "Amateur"


class Task(LongPlayScrobblableMixin):
    """Basically a holder for task sources ... Shortcut, JIRA, Todoist, Org-mode
    and any other otherwise generic tasks.

    """

    source = models.CharField(max_length=255, **BNULL)
    source_url_pattern = models.CharField(
        max_length=255, choices=TASK_SOURCE_URL_PATTERNS, **BNULL
    )
    description = models.TextField(**BNULL)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("tasks:task_detail", kwargs={"slug": self.uuid})

    @property
    def logdata_cls(self):
        return TaskLogData

    def source_url_for_user(self, user_id):
        url = str(self.source_url_pattern).replace("{id}", "")
        scrobble = self.scrobbles(user_id).first()
        if scrobble.logdata.source_id and self.source_url_pattern:
            url = str(self.source_url_pattern).format(
                id=scrobble.logdata.source_id
            )

        return url

    def subtitle_for_user(self, user_id):
        scrobble = self.scrobbles(user_id).first()
        return scrobble.logdata.source_id or ""

    @classmethod
    def find_or_create(cls, title: str) -> "Task":
        return cls.objects.filter(title=title).first()

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(user_id=user_id, task=self).order_by(
            "-timestamp"
        )
