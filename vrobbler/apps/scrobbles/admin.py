from django.contrib import admin

from scrobbles.models import Scrobble


class ScrobbleAdmin(admin.ModelAdmin):
    date_hierarchy = "timestamp"
    list_display = (
        "timestamp",
        "video",
        "track",
        "source",
        "playback_position",
        "in_progress",
    )
    list_filter = ("in_progress", "source", "track__artist")
    ordering = ("-timestamp",)


admin.site.register(Scrobble, ScrobbleAdmin)
