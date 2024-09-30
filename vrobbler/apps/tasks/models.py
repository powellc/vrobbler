from enum import Enum
from typing import Optional
from django.apps import apps
from django.db import models
from django.urls import reverse
from scrobbles.dataclasses import LongPlayLogData
from scrobbles.mixins import ScrobblableMixin

BNULL = {"blank": True, "null": True}


class TaskLogData(LongPlayLogData):
    serial_scrobble_id: Optional[int]
    long_play_complete: bool = False


class TaskType(Enum):
    WOODS = "Professional"
    ROAD = "Amateur"


class Task(ScrobblableMixin):
    """Basically a holder for task sources ... Shortcut, JIRA, Todoist, Org-mode
    and any other otherwise generic tasks.

    """

    description = models.TextField(**BNULL)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("tasks:task_detail", kwargs={"slug": self.uuid})

    @property
    def logdata_cls(self):
        return TaskLogData

    @classmethod
    def find_or_create(cls, title: str) -> "Task":
        return cls.objects.filter(title=title).first()

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(user_id=user_id, task=self).order_by(
            "-timestamp"
        )
