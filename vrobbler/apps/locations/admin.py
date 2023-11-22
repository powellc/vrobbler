from django.contrib import admin

from locations.models import GeoLocation, RawGeoLocation

from scrobbles.admin import ScrobbleInline


@admin.register(GeoLocation)
class GeoLocationAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "lat",
        "lon",
        "title",
        "altitude",
    )
    ordering = (
        "lat",
        "lon",
    )


@admin.register(RawGeoLocation)
class RawGeoLocationAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "lat",
        "lon",
        "altitude",
        "speed",
    )
    ordering = (
        "lat",
        "lon",
    )
