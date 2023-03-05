from datetime import timedelta

import pytz
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import TimeStampedModel
from encrypted_field import EncryptedField
from profiles.constants import PRETTY_TIMEZONE_CHOICES

from vrobbler.apps.videogames.igdb import refresh_igdb_api_token

User = get_user_model()
BNULL = {"blank": True, "null": True}


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    timezone = models.CharField(
        max_length=255,
        choices=PRETTY_TIMEZONE_CHOICES,
        **BNULL,
    )
    lastfm_username = models.CharField(max_length=255, **BNULL)
    lastfm_password = EncryptedField(**BNULL)
    twitch_client_id = models.CharField(max_length=255, **BNULL)
    twitch_client_secret = EncryptedField(**BNULL)
    twitch_token = EncryptedField(**BNULL)
    twitch_token_expires = models.DateTimeField(**BNULL)

    def __str__(self):
        return f"User profile for {self.user}"

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)

    def get_twitch_token(self):
        now = timezone.now()
        token = self.twitch_token
        if not token or self.twitch_token_expires < now:
            self.twitch_token, expires_in = refresh_igdb_api_token(
                self.user_id
            )
            self.twitch_token_expires = now + timedelta(seconds=expires_in)
            self.save(update_fields=["twitch_token", "twitch_token_expires"])
        return self.twitch_token
