from django.core.files.base import ContentFile
import requests
from typing import Optional
from books.openlibrary import (
    lookup_author_from_openlibrary,
    lookup_book_from_openlibrary,
)
from books.models import Author, Book


def update_or_create_book(
    title: str, author: Optional[str] = None, force_update=False
) -> Book:
    book_dict = lookup_book_from_openlibrary(title, author)

    book, book_created = Book.objects.get_or_create(
        isbn=book_dict.get("isbn"),
    )

    if book_created or force_update:
        cover_url = book_dict.pop("cover_url")
        ol_author_id = book_dict.pop("ol_author_id")

        Book.objects.filter(pk=book.id).update(**book_dict)
        book.refresh_from_db()

        # Process authors
        author_dict = lookup_author_from_openlibrary(ol_author_id)
        author = Author.objects.filter(openlibrary_id=ol_author_id).first()
        if not author:
            author_image_url = author_dict.pop("author_headshot_url", None)

            author = Author.objects.create(**author_dict)

            if author_image_url:
                r = requests.get(author_image_url)
                if r.status_code == 200:
                    fname = f"{author.name}_{author.uuid}.jpg"
                    author.headshot.save(
                        fname, ContentFile(r.content), save=True
                    )
        book.authors.add(author)

        # Process cover URL
        r = requests.get(cover_url)
        if r.status_code == 200:
            fname = f"{book.title}_{book.uuid}.jpg"
            book.cover.save(fname, ContentFile(r.content), save=True)

        book.fix_metadata()

    return book
