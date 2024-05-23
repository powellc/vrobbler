from django.contrib import admin

from lifeevents.models import LifeEvent

from scrobbles.admin import ScrobbleInline


@admin.register(LifeEvent)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("title",)
    search_fields = ("title",)
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
