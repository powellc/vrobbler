from django.contrib import admin

from books.models import Author, Book

from scrobbles.admin import ScrobbleInline


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "openlibrary_id")
    ordering = ("-created",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "title",
        "isbn",
        "first_publish_year",
        "pages",
        "openlibrary_id",
    )
    search_fields = ("name",)
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
