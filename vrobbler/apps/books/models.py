import logging
from datetime import timedelta
from typing import Optional
from uuid import uuid4

import requests
from books.openlibrary import (
    lookup_author_from_openlibrary,
    lookup_book_from_openlibrary,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import LongPlayScrobblableMixin, ScrobblableMixin
from scrobbles.utils import get_scrobbles_for_media

logger = logging.getLogger(__name__)
User = get_user_model()
BNULL = {"blank": True, "null": True}


class Author(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    openlibrary_id = models.CharField(max_length=255, **BNULL)
    headshot = models.ImageField(upload_to="books/authors/", **BNULL)
    bio = models.TextField(**BNULL)
    wikipedia_url = models.CharField(max_length=255, **BNULL)
    isni = models.CharField(max_length=255, **BNULL)
    wikidata_id = models.CharField(max_length=255, **BNULL)
    goodreads_id = models.CharField(max_length=255, **BNULL)
    librarything_id = models.CharField(max_length=255, **BNULL)
    amazon_id = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return f"{self.name}"

    def fix_metadata(self, data_dict: dict = {}):
        if not data_dict and self.openlibrary_id:
            data_dict = lookup_author_from_openlibrary(self.openlibrary_id)

        if not data_dict or not data_dict.get("name"):
            return

        headshot_url = data_dict.pop("author_headshot_url", "")

        Author.objects.filter(pk=self.id).update(**data_dict)
        self.refresh_from_db()

        if headshot_url:
            r = requests.get(headshot_url)
            if r.status_code == 200:
                fname = f"{self.name}_{self.uuid}.jpg"
                self.headshot.save(fname, ContentFile(r.content), save=True)


class Book(LongPlayScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "BOOK_COMPLETION_PERCENT", 95)
    AVG_PAGE_READING_SECONDS = getattr(
        settings, "AVERAGE_PAGE_READING_SECONDS", 60
    )

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
    first_sentence = models.CharField(max_length=255, **BNULL)
    openlibrary_id = models.CharField(max_length=255, **BNULL)
    cover = models.ImageField(upload_to="books/covers/", **BNULL)

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def subtitle(self):
        return f" by {self.author}"

    @property
    def primary_image(self) -> Optional["ImageField"]:
        img = None
        if self.cover:
            img = self.cover
        return img

    def get_start_url(self):
        return reverse("scrobbles:start", kwargs={"uuid": self.uuid})

    def get_absolute_url(self):
        return reverse("books:book_detail", kwargs={"slug": self.uuid})

    def fix_metadata(self, force_update=False):
        if not self.openlibrary_id or force_update:
            author_name = ""
            if self.author:
                author_name = self.author.name
            book_dict = lookup_book_from_openlibrary(self.title, author_name)
            if not book_dict:
                logger.warn(f"Book not found in OL {self.title}")
                return

            cover_url = book_dict.pop("cover_url", "")
            ol_author_id = book_dict.pop("ol_author_id", "")
            ol_author_name = book_dict.pop("ol_author_name", "")
            if book_dict.get("pages") == None:
                book_dict.pop("pages")

            ol_title = book_dict.get("title")

            if ol_title.lower() != self.title.lower():
                logger.warn(
                    f"OL and KoReader disagree on this book title {self.title} != {ol_title}"
                )

            Book.objects.filter(pk=self.id).update(**book_dict)
            self.refresh_from_db()

            # Process authors
            author = None
            author_created = False
            if ol_author_id:
                author, author_created = Author.objects.get_or_create(
                    openlibrary_id=ol_author_id
                )
                if author_created or force_update:
                    author.fix_metadata()
            if not author and ol_author_name:
                author, author_created = Author.objects.get_or_create(
                    name=ol_author_name
                )
            self.authors.add(author)

            if cover_url:
                r = requests.get(cover_url)
                if r.status_code == 200:
                    fname = f"{self.title}_{self.uuid}.jpg"
                    self.cover.save(fname, ContentFile(r.content), save=True)

            if self.pages:
                self.run_time_seconds = self.pages * int(
                    self.AVG_PAGE_READING_SECONDS
                )

            self.save()

    @property
    def author(self):
        return self.authors.first()

    @property
    def pages_for_completion(self) -> int:
        if not self.pages:
            logger.warn(f"{self} has no pages, no completion percentage")
            return 0
        return int(self.pages * (self.COMPLETION_PERCENT / 100))

    def update_long_play_seconds(self):
        """Check page timestamps and duration and update"""
        if self.page_set.all():
            ...

    def progress_for_user(self, user_id: int) -> int:
        """Used to keep track of whether the book is complete or not"""
        user = User.objects.get(id=user_id)
        last_scrobble = get_scrobbles_for_media(self, user).last()
        progress = 0
        if last_scrobble:
            progress = int((last_scrobble.book_pages_read / self.pages) * 100)
        return progress

    @classmethod
    def find_or_create(cls, data_dict: dict) -> "Game":
        from books.utils import update_or_create_book

        return update_or_create_book(
            data_dict.get("title"), data_dict.get("author")
        )


class Page(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    number = models.IntegerField()
    start_time = models.DateTimeField(**BNULL)
    end_time = models.DateTimeField(**BNULL)
    duration_seconds = models.IntegerField(**BNULL)

    class Meta:
        unique_together = (
            "book",
            "number",
        )

    def __str__(self):
        return f"Page {self.number} of {self.book.pages} in {self.book.title}"

    def save(self, *args, **kwargs):
        if not self.end_time and self.duration_seconds:
            self._set_end_time()

        return super(Page, self).save(*args, **kwargs)

    @property
    def next(self):
        page = self.book.page_set.filter(number=self.number + 1).first()
        if not page:
            page = (
                self.book.page_set.filter(created__gt=self.created)
                .order_by("created")
                .first()
            )
        return page

    @property
    def previous(self):
        page = self.book.page_set.filter(number=self.number - 1).first()
        if not page:
            page = (
                self.book.page_set.filter(created__lt=self.created)
                .order_by("-created")
                .first()
            )
        return page

    @property
    def seconds_to_next_page(self) -> int:
        seconds = 999999  # Effectively infnity time as we have no next
        if not self.end_time:
            self._set_end_time()
        if self.next:
            seconds = (self.next.start_time - self.end_time).seconds
        return seconds

    @property
    def is_scrobblable(self) -> bool:
        """A page defines the start of a scrobble if the seconds to next page
        are greater than an hour, or 3600 seconds, and it's not a single page,
        so the next seconds to next_page is less than an hour as well.

        As a special case, the first recorded page is a scrobble, so we establish
        when the book was started.

        """
        is_scrobblable = False
        over_an_hour_since_last_page = False
        if not self.previous:
            is_scrobblable = True

        if self.previous:
            over_an_hour_since_last_page = (
                self.previous.seconds_to_next_page >= 3600
            )
        blip = self.seconds_to_next_page >= 3600

        if over_an_hour_since_last_page and not blip:
            is_scrobblable = True
        return is_scrobblable

    def _set_end_time(self) -> None:
        if self.end_time:
            return

        self.end_time = self.start_time + timedelta(
            seconds=self.duration_seconds
        )
        self.save(update_fields=["end_time"])
