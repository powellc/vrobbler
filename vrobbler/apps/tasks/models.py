from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.apps import apps
from django.db import models
from django.urls import reverse
from scrobbles.dataclasses import LongPlayLogData
from scrobbles.mixins import LongPlayScrobblableMixin

BNULL = {"blank": True, "null": True}

TODOIST_TASK_URL = "https://app.todoist.com/app/task/{id}"


@dataclass
class TaskLogData(LongPlayLogData):
    details: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    project: Optional[str] = None
    todoist_id: Optional[str] = None
    todoist_event: Optional[str] = None
    todoist_type: Optional[str] = None
    serial_scrobble_id: Optional[int] = None
    long_play_complete: Optional[bool] = None
    timestamp_utc: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: Optional[list[dict]] = None


class Task(LongPlayScrobblableMixin):
    """Basically a holder for Todoist Tasks
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

    def source_url_for_user(self, user_id) -> str:
        url = ""
        scrobble = self.scrobbles(user_id).first()
        if scrobble:
            url = TODOIST_TASK_URL.format(id=scrobble.logdata.todoist_id)
        return url

    def subtitle_for_user(self, user_id):
        scrobble = self.scrobbles(user_id).first()
        return scrobble.logdata.description or ""

    @classmethod
    def find_or_create(cls, title: str) -> "Task":
        task, created = cls.objects.get_or_create(title=title)
        if created:
            task.run_time_seconds = 1800
            task.save(update_fields=["run_time_seconds"])

        return task

    def scrobbles(self, user_id):
        Scrobble = apps.get_model("scrobbles", "Scrobble")
        return Scrobble.objects.filter(user_id=user_id, task=self).order_by(
            "-timestamp"
        )
