from django.contrib import admin

from moods.models import Mood
from scrobbles.admin import ScrobbleInline


class MoodInline(admin.TabularInline):
    model = Mood
    extra = 0


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
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
