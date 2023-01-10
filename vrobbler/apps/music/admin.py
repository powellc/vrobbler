from django.contrib import admin

from music.models import Artist, Album, Track


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "year", "musicbrainz_id")
    list_filter = ("year",)
    ordering = ("name",)


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
