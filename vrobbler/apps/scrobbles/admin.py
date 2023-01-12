from django.contrib import admin

from scrobbles.models import Scrobble


@admin.register(Scrobble)
class ScrobbleAdmin(admin.ModelAdmin):
    date_hierarchy = "timestamp"
    list_display = (
        "timestamp",
        "media_name",
        "media_type",
        "source",
        "playback_position",
        "in_progress",
        "is_paused",
    )
    list_filter = ("is_paused", "in_progress", "source", "track__artist")
    ordering = ("-timestamp",)

    def media_name(self, obj):
        if obj.video:
            return obj.video
        if obj.track:
            return obj.track
        if obj.podcast_episode:
            return obj.podcast_episode

    def media_type(self, obj):
        if obj.video:
            return "Video"
        if obj.track:
            return "Track"
        if obj.podcast_episode:
            return "Podcast"
