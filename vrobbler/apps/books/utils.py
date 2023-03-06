from django.core.files.base import ContentFile
import requests
from typing import Optional
from books.openlibrary import lookup_book_from_openlibrary
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
        ol_author_name = book_dict.pop("ol_author_name")
        author_image_url = book_dict.pop("author_image_url")

        Book.objects.filter(pk=book.id).update(**book_dict)
        book.refresh_from_db()

        # Process authors
        if ol_author_name and ol_author_id:
            author, author_created = Author.objects.get_or_create(
                name=ol_author_name
            )
            if author_created or force_update:
                author.openlibrary_id = ol_author_id
                author.save()

                r = requests.get(author_image_url)
                if r.status_code == 200:
                    fname = f"{author.name}_{author.uuid}.jpg"
                    author.headshot.save(
                        fname, ContentFile(r.content), save=True
                    )

        # Process cover URL
        r = requests.get(cover_url)
        if r.status_code == 200:
            fname = f"{book.title}_{book.uuid}.jpg"
            book.cover.save(fname, ContentFile(r.content), save=True)

        book.fix_metadata()

    return book
