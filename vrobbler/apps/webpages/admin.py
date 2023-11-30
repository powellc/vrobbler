from django.contrib import admin

from webpages.models import WebPage

from scrobbles.admin import ScrobbleInline


@admin.register(WebPage)
class WebPageAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "title",
        "url",
    )
    ordering = ("-created",)
    search_fields = ("title",)
    inlines = [
        ScrobbleInline,
    ]
