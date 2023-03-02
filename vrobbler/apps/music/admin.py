from django.contrib import admin

from music.models import Artist, Album, Track

from scrobbles.admin import ScrobbleInline


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "name",
        "year",
        "primary_artist",
        "theaudiodb_genre",
        "theaudiodb_mood",
        "musicbrainz_id",
    )
    list_filter = (
        "theaudiodb_score",
        "theaudiodb_genre",
    )
    ordering = ("name",)
    filter_horizontal = [
        'artists',
    ]


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "musicbrainz_id")
    ordering = ("name",)


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "title",
        "album",
        "artist",
        "run_time",
        "musicbrainz_id",
    )
    list_filter = ("album", "artist")
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
