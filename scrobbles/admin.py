from django.contrib import admin

from scrobbles.models import Scrobble


class ScrobbleAdmin(admin.ModelAdmin):
    date_hierarchy = "timestamp"
    list_display = (
        "video",
        "timestamp",
        "source",
        "playback_position",
        "in_progress",
    )
    list_filter = ("video",)
    ordering = ("-timestamp",)


admin.site.register(Scrobble, ScrobbleAdmin)
