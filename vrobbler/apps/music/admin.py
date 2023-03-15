from django.contrib import admin

from music.models import Artist, Album, Track

from scrobbles.admin import ScrobbleInline


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "name",
        "year",
        "album_artist",
        "theaudiodb_genre",
        "theaudiodb_mood",
        "musicbrainz_id",
    )
    list_filter = (
        "theaudiodb_score",
        "theaudiodb_genre",
    )
    ordering = ("-created",)
    search_fields = ("name",)
    filter_horizontal = [
        "artists",
    ]


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "name",
        "theaudiodb_mood",
        "theaudiodb_genre",
        "musicbrainz_id",
    )
    list_filter = (
        "theaudiodb_mood",
        "theaudiodb_genre",
    )
    search_fields = ("name",)
    ordering = ("-created",)


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "title",
        "album",
        "artist",
        "musicbrainz_id",
    )
    list_filter = ("album", "artist")
    search_fields = ("title",)
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
