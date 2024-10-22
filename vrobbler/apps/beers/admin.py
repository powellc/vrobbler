from beers.models import Beer, BeerProducer, BeerStyle
from django.contrib import admin
from scrobbles.admin import ScrobbleInline


class BeerInline(admin.TabularInline):
    model = Beer
    extra = 0


@admin.register(BeerStyle)
class BeerStyle(admin.ModelAdmin):
    date_hierarchy = "created"
    search_fields = ("name",)


@admin.register(BeerProducer)
class BeerProducer(admin.ModelAdmin):
    date_hierarchy = "created"
    search_fields = ("name",)


@admin.register(Beer)
class BeerAdmin(admin.ModelAdmin):
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
