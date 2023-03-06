from django.contrib import admin

from videogames.models import VideoGame, VideoGamePlatform

from scrobbles.admin import ScrobbleInline


@admin.register(VideoGamePlatform)
class VideoGamePlatformAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "name",
        "igdb_id",
        "uuid",
    )
    ordering = ("-created",)


@admin.register(VideoGame)
class GameAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "hltb_id",
        "title",
        "hltb_score",
        "main_story_time",
        "release_year",
    )
    search_fields = (
        "title",
        "alternative_name",
    )
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
