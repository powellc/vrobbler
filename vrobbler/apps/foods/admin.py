from foods.models import Food, FoodCategory
from django.contrib import admin
from scrobbles.admin import ScrobbleInline


class FoodInline(admin.TabularInline):
    model = Food
    extra = 0


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    search_fields = ("name",)


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
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
