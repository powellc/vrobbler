from django.contrib import admin

from scrobbles.models import (
    AudioScrobblerTSVImport,
    ChartRecord,
    KoReaderImport,
    LastFmImport,
    RetroarchImport,
    Scrobble,
    ScrobbledPage,
)
from scrobbles.mixins import Genre


class ScrobbleInline(admin.TabularInline):
    model = Scrobble
    extra = 0
    raw_id_fields = (
        "video",
        "podcast_episode",
        "track",
        "video_game",
        "book",
        "sport_event",
        "user",
    )
    exclude = ("source_id", "scrobble_log")


class ImportBaseAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "uuid",
        "process_count",
        "processed_finished",
        "processing_started",
    )
    ordering = ("-created",)


@admin.register(AudioScrobblerTSVImport)
class AudioScrobblerTSVImportAdmin(ImportBaseAdmin):
    ...


@admin.register(LastFmImport)
class LastFmImportAdmin(ImportBaseAdmin):
    ...


@admin.register(KoReaderImport)
class KoReaderImportAdmin(ImportBaseAdmin):
    ...


@admin.register(RetroarchImport)
class RetroarchImportAdmin(ImportBaseAdmin):
    ...


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "source",
    )


@admin.register(ChartRecord)
class ChartRecordAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "user",
        "rank",
        "count",
        "year",
        "week",
        "month",
        "day",
        "media_name",
    )
    ordering = ("-created",)

    def media_name(self, obj):
        return obj.media_obj


@admin.register(Scrobble)
class ScrobbleAdmin(admin.ModelAdmin):
    date_hierarchy = "timestamp"
    list_display = (
        "timestamp",
        "media_name",
        "media_type",
        "playback_percent",
        "source",
        "in_progress",
        "is_paused",
        "played_to_completion",
    )
    raw_id_fields = (
        "video",
        "podcast_episode",
        "track",
        "sport_event",
        "book",
        "video_game",
    )
    list_filter = (
        "is_paused",
        "in_progress",
        "media_type",
        "long_play_complete",
        "source",
    )
    ordering = ("-timestamp",)

    def media_name(self, obj):
        return obj.media_obj

    def playback_percent(self, obj):
        return obj.percent_played


@admin.register(ScrobbledPage)
class ScrobbledPageAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "scrobble",
        "notes",
    )
    raw_id_fields = ("scrobble",)
