from django.contrib import admin

from tasks.models import Task

from scrobbles.admin import ScrobbleInline


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
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
