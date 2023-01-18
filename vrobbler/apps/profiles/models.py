from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import TimeStampedModel
from profiles.constants import PRETTY_TIMEZONE_CHOICES

User = get_user_model()


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    timezone = models.CharField(
        max_length=255, choices=PRETTY_TIMEZONE_CHOICES
    )

    def __str__(self):
        return f"User profile for {self.user}"
