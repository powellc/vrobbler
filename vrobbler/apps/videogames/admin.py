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
    list_display = ("title", "igdb_id")
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
