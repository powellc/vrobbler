from django.contrib import admin

from videos.models import Series, Video


class SeriesAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "tagline")
    ordering = ("-created",)


class VideoAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
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


admin.site.register(Series, SeriesAdmin)
admin.site.register(Video, VideoAdmin)
