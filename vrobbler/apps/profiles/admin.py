from django.contrib import admin

from profiles.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    ordering = ("-created",)
    exclude = (
        "twitch_token",
        "twitch_client_secret",
        "lastfm_password",
        "archivebox_password",
    )
