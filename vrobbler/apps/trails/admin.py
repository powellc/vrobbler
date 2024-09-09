from django.contrib import admin

from trails.models import Trail

from scrobbles.admin import ScrobbleInline


class TrailInline(admin.TabularInline):
    model = Trail
    extra = 0


@admin.register(Trail)
class TrailAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "uuid",
        "title",
        "trailhead_location",
    )
    raw_id_fields = (
        "trailhead_location",
        "trail_terminus_location",
    )
    ordering = ("-created",)
    search_fields = ("title",)
    inlines = [
        ScrobbleInline,
    ]
