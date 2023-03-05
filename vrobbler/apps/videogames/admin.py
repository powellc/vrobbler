from django.contrib import admin

from videogames.models import VideoGame, VideoGameCollection

from scrobbles.admin import ScrobbleInline


@admin.register(VideoGameCollection)
class VideoGameCollectionAdmin(admin.ModelAdmin):
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
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
