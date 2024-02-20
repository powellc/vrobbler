from django.contrib import admin

from locations.models import GeoLocation

from scrobbles.admin import ScrobbleInline


@admin.register(GeoLocation)
class GeoLocationAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "created",
        "lat",
        "lon",
        "title",
        "altitude",
    )
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
