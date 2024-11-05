from datetime import timedelta

import pytz
from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import TimeStampedModel
from encrypted_field import EncryptedField
from profiles.constants import PRETTY_TIMEZONE_CHOICES

User = get_user_model()
BNULL = {"blank": True, "null": True}


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    timezone = models.CharField(
        max_length=255, choices=PRETTY_TIMEZONE_CHOICES, default="UTC"
    )
    lastfm_username = models.CharField(max_length=255, **BNULL)
    lastfm_password = EncryptedField(**BNULL)
    lastfm_auto_import = models.BooleanField(default=False)

    retroarch_path = models.CharField(max_length=255, **BNULL)
    retroarch_auto_import = models.BooleanField(default=False)

    archivebox_username = models.CharField(max_length=255, **BNULL)
    archivebox_password = EncryptedField(**BNULL)
    archivebox_url = models.CharField(max_length=255, **BNULL)

    bgg_username = models.CharField(max_length=255, **BNULL)

    todoist_auth_key = EncryptedField(**BNULL)
    todoist_state = EncryptedField(**BNULL)
    todoist_user_id = models.CharField(max_length=100, **BNULL)

    webdav_url = models.CharField(max_length=255, **BNULL)
    webdav_user = models.CharField(max_length=255, **BNULL)
    webdav_pass = EncryptedField(**BNULL)
    webdav_auto_import = models.BooleanField(default=False)

    ntfy_url = models.CharField(max_length=255, **BNULL)
    ntfy_enabled = models.BooleanField(default=False)

    redirect_to_webpage = models.BooleanField(default=True)

    def __str__(self):
        return f"User profile for {self.user}"

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)
