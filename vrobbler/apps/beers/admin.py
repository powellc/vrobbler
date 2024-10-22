from django.contrib import admin

from beers.models import Beer

from scrobbles.admin import ScrobbleInline


class BeerInline(admin.TabularInline):
    model = Beer
    extra = 0


@admin.register(Beer)
class BeerProducer(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("uuid",)
    search_fields = ("name",)


@admin.register(Beer)
class BeerAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "uuid",
        "title",
        "style",
    )
    ordering = ("-created",)
    search_fields = ("title",)
    inlines = [
        ScrobbleInline,
    ]
