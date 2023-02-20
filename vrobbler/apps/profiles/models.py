import pytz

from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import TimeStampedModel
from profiles.constants import PRETTY_TIMEZONE_CHOICES

from encrypted_field import EncryptedField

User = get_user_model()
BNULL = {"blank": True, "null": True}


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    timezone = models.CharField(
        max_length=255, choices=PRETTY_TIMEZONE_CHOICES, default=pytz.UTC
    )
    lastfm_username = models.CharField(max_length=255, **BNULL)
    lastfm_password = EncryptedField(**BNULL)

    def __str__(self):
        return f"User profile for {self.user}"

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)
