from django.core.files.base import ContentFile
import requests
from typing import Optional
from books.openlibrary import lookup_book_from_openlibrary
from books.models import Book


def get_or_create_book(title: str, author: Optional[str] = None) -> Book:
    book_dict = lookup_book_from_openlibrary(title, author)

    book, book_created = Book.objects.get_or_create(
        isbn=book_dict.get("isbn"),
    )

    if book_created:
        cover_url = book_dict.pop("cover_url")

        Book.objects.filter(pk=book.id).update(**book_dict)
        book.refresh_from_db()

        r = requests.get(cover_url)
        if r.status_code == 200:
            fname = f"{book.title}_{book.uuid}.jpg"
            book.cover.save(fname, ContentFile(r.content), save=True)

        book.fix_metadata()

    return book
