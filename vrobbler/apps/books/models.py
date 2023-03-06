import logging

from books.openlibrary import lookup_book_from_openlibrary
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin
from scrobbles.utils import get_scrobbles_for_media

logger = logging.getLogger(__name__)
User = get_user_model()
BNULL = {"blank": True, "null": True}


class Author(TimeStampedModel):
    name = models.CharField(max_length=255)
    openlibrary_id = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return f"{self.name}"

    def fix_metadata(self):
        logger.warn("Not implemented yet")


class Book(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "BOOK_COMPLETION_PERCENT", 95)

    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author)
    goodreads_id = models.CharField(max_length=255, **BNULL)
    koreader_id = models.IntegerField(**BNULL)
    koreader_authors = models.CharField(max_length=255, **BNULL)
    koreader_md5 = models.CharField(max_length=255, **BNULL)
    isbn = models.CharField(max_length=255, **BNULL)
    pages = models.IntegerField(**BNULL)
    language = models.CharField(max_length=4, **BNULL)
    first_publish_year = models.IntegerField(**BNULL)
    author_name = models.CharField(max_length=255, **BNULL)
    author_openlibrary_id = models.CharField(max_length=255, **BNULL)
    openlibrary_id = models.CharField(max_length=255, **BNULL)
    cover = models.ImageField(upload_to="books/covers/", **BNULL)

    def __str__(self):
        return f"{self.title} by {self.author}"

    def fix_metadata(self):
        if not self.openlibrary_id:
            book_meta = lookup_book_from_openlibrary(self.title, self.author)
            self.openlibrary_id = book_meta.get("openlibrary_id")
            self.isbn = book_meta.get("isbn")
            self.goodreads_id = book_meta.get("goodreads_id")
            self.first_pubilsh_year = book_meta.get("first_publish_year")
            self.save()

    @property
    def author(self):
        return self.authors.first()

    def get_absolute_url(self):
        return reverse("books:book_detail", kwargs={"slug": self.uuid})

    @property
    def pages_for_completion(self) -> int:
        if not self.pages:
            logger.warn(f"{self} has no pages, no completion percentage")
            return 0
        return int(self.pages * (self.COMPLETION_PERCENT / 100))

    def progress_for_user(self, user_id: int) -> int:
        """Used to keep track of whether the book is complete or not"""
        user = User.objects.get(id=user_id)
        last_scrobble = get_scrobbles_for_media(self, user).last()
        return int((last_scrobble.book_pages_read / self.pages) * 100)

    @classmethod
    def find_or_create(cls, data_dict: dict) -> "Game":
        from books.utils import get_or_create_book

        return get_or_create_book(
            data_dict.get("title"), data_dict.get("author")
        )
