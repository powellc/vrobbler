from django.contrib.auth import get_user_model
from django.db.models.base import post_save
from django.dispatch import receiver

from profiles.models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
