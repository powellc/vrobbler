from django.contrib import admin
from scrobbles.models import (
    AudioScrobblerTSVImport,
    ChartRecord,
    KoReaderImport,
    LastFmImport,
    Scrobble,
)


class ScrobbleInline(admin.TabularInline):
    model = Scrobble
    extra = 0
    raw_id_fields = ('video', 'podcast_episode', 'track')
    exclude = ('source_id', 'scrobble_log')


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
    """"""


@admin.register(LastFmImport)
class LastFmImportAdmin(ImportBaseAdmin):
    """"""


@admin.register(KoReaderImport)
class KoReaderImportAdmin(ImportBaseAdmin):
    """"""


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
        if obj.video:
            return obj.video
        if obj.track:
            return obj.track
        if obj.podcast_episode:
            return obj.podcast_episode
        if obj.sport_event:
            return obj.sport_event


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
        'video',
        'podcast_episode',
        'track',
        'sport_event',
        'book',
    )
    list_filter = ("is_paused", "in_progress", "source", "track__artist")
    ordering = ("-timestamp",)

    def media_name(self, obj):
        return obj.media_obj

    def media_type(self, obj):
        return obj.media_obj.__class__.__name__
        if obj.video:
            return "Video"
        if obj.track:
            return "Track"
        if obj.podcast_episode:
            return "Podcast"
        if obj.sport_event:
            return "Sport Event"

    def playback_percent(self, obj):
        return obj.percent_played
