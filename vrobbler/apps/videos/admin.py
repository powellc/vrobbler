from django.contrib import admin
from scrobbles.models import Scrobble
from videos.models import Series, Video
from scrobbles.admin import ScrobbleInline


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "tagline")
    ordering = ("-created",)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    raw_id_fields = ('tv_series',)
    list_display = (
        "title",
        "video_type",
        "year",
        "tv_series",
        "season_number",
        "episode_number",
        "imdb_id",
    )
    list_filter = ("year", "tv_series", "video_type")
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
