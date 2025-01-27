from django.contrib import admin

from books.models import Author, Book, Page

from scrobbles.admin import ScrobbleInline


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "name",
        "openlibrary_id",
        "bio",
        "wikipedia_url",
    )
    ordering = ("-created",)
    search_fields = ("name",)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_filter = ("book",)
    ordering = ("book", "number")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "title",
        "subtitle",
        "isbn_13",
        "first_publish_year",
        "pages",
    )
    search_fields = ("name",)
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
