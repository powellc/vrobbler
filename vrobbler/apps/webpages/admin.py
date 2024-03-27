from django.contrib import admin

from webpages.models import Domain, WebPage

from scrobbles.admin import ScrobbleInline


class WebPageInline(admin.TabularInline):
    model = WebPage
    extra = 0

    exclude = ("extract",)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    ordering = ("root",)

    inlines = [WebPageInline]


@admin.register(WebPage)
class WebPageAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "uuid",
        "title",
        "url",
    )
    raw_id_fields = ("domain",)
    ordering = ("-created",)
    search_fields = ("title",)
    inlines = [
        ScrobbleInline,
    ]
