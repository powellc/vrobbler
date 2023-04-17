from django.contrib import admin

from boardgames.models import BoardGame, BoardGamePublisher

from scrobbles.admin import ScrobbleInline


@admin.register(BoardGamePublisher)
class BoardGamePublisherAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "name",
        "uuid",
    )
    ordering = ("-created",)


@admin.register(BoardGame)
class GameAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "bggeek_id",
        "title",
        "published_date",
    )
    search_fields = ("title",)
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
