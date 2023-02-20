from django.contrib import admin

from books.models import Author, Book

from scrobbles.admin import ScrobbleInline


@admin.register(Author)
class AlbumAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "openlibrary_id")
    ordering = ("name",)


@admin.register(Book)
class ArtistAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "title",
        "isbn",
        "first_publish_year",
        "pages",
        "openlibrary_id",
    )
    ordering = ("title",)
