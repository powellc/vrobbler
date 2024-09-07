from django.contrib import admin

from bricksets.models import BrickSet
from scrobbles.admin import ScrobbleInline


class BrickSetInline(admin.TabularInline):
    model = BrickSet
    extra = 0


@admin.register(BrickSet)
class BrickSetAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "uuid",
        "title",
    )
    ordering = ("-created",)
    search_fields = ("title",)
    inlines = [
        ScrobbleInline,
    ]
