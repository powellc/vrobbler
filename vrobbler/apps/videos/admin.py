from django.contrib import admin
from scrobbles.models import Scrobble
from videos.models import Series, Video, Channel
from scrobbles.admin import ScrobbleInline


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "youtube_id")
    ordering = ("-created",)


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "imdb_id")
    ordering = ("-created",)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    raw_id_fields = ("tv_series","channel",)
    list_display = (
        "title",
        "video_type",
        "year",
        "tv_series",
        "channel",
        "imdb_rating",
    )
    list_filter = ("year", "tv_series", "channel", "video_type")
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
