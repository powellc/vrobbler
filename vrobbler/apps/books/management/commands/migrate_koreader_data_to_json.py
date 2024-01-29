from django.core.management.base import BaseCommand
from books.models import Book


class Command(BaseCommand):
    def handle(self, *args, **options):
        for book in Book.objects.all():
            koreader_data = book.koreader_data_by_hash or {}
            if book.koreader_md5:
                koreader_data[book.koreader_md5] = {
                    "title": book.title,
                    "book_id": book.koreader_id,
                    "author_str": book.koreader_authors,
                    "pages": book.pages,
                }
            book.koreader_data_by_hash = koreader_data
            book.save(update_fields=["koreader_data_by_hash"])
