from collections import OrderedDict
import logging
from datetime import timedelta, datetime
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
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from scrobbles.mixins import (
    LongPlayScrobblableMixin,
    ObjectWithGenres,
    ScrobblableMixin,
)
from scrobbles.utils import get_scrobbles_for_media
from taggit.managers import TaggableManager
from thefuzz import fuzz
from vrobbler.apps.books.comicvine import (
    ComicVineClient,
    lookup_comic_from_comicvine,
)

from vrobbler.apps.books.locg import (
    lookup_comic_by_locg_slug,
    lookup_comic_from_locg,
    lookup_comic_writer_by_locg_slug,
)
from vrobbler.apps.scrobbles.dataclasses import BookLogData

COMICVINE_API_KEY = getattr(settings, "COMICVINE_API_KEY", "")

logger = logging.getLogger(__name__)
User = get_user_model()
BNULL = {"blank": True, "null": True}


class Author(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    openlibrary_id = models.CharField(max_length=255, **BNULL)
    headshot = models.ImageField(upload_to="books/authors/", **BNULL)
    headshot_small = ImageSpecField(
        source="headshot",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    headshot_medium = ImageSpecField(
        source="headshot",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    bio = models.TextField(**BNULL)
    wikipedia_url = models.CharField(max_length=255, **BNULL)
    isni = models.CharField(max_length=255, **BNULL)
    locg_slug = models.CharField(max_length=255, **BNULL)
    wikidata_id = models.CharField(max_length=255, **BNULL)
    goodreads_id = models.CharField(max_length=255, **BNULL)
    librarything_id = models.CharField(max_length=255, **BNULL)
    comicvine_data = models.JSONField(**BNULL)
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
    authors = models.ManyToManyField(Author, blank=True)
    goodreads_id = models.CharField(max_length=255, **BNULL)
    koreader_data_by_hash = models.JSONField(**BNULL)
    isbn = models.CharField(max_length=255, **BNULL)
    pages = models.IntegerField(**BNULL)
    language = models.CharField(max_length=4, **BNULL)
    first_publish_year = models.IntegerField(**BNULL)
    first_sentence = models.TextField(**BNULL)
    openlibrary_id = models.CharField(max_length=255, **BNULL)
    locg_slug = models.CharField(max_length=255, **BNULL)
    comicvine_data = models.JSONField(**BNULL)
    cover = models.ImageField(upload_to="books/covers/", **BNULL)
    cover_small = ImageSpecField(
        source="cover",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    cover_medium = ImageSpecField(
        source="cover",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 75},
    )
    summary = models.TextField(**BNULL)

    genre = TaggableManager(through=ObjectWithGenres)

    def __str__(self):
        return f"{self.title}"

    @property
    def subtitle(self):
        return f" by {self.author}"

    @property
    def verb(self) -> str:
        return "Reading"

    @property
    def logdata_cls(self):
        return BookLogData

    @property
    def primary_image_url(self) -> str:
        url = ""
        if self.cover:
            url = self.cover_medium.url
        return url

    def get_start_url(self):
        return reverse("scrobbles:start", kwargs={"uuid": self.uuid})

    def get_absolute_url(self):
        return reverse("books:book_detail", kwargs={"slug": self.uuid})

    def fix_metadata(self, data: dict = {}, force_update=False):
        if (not self.openlibrary_id or not self.locg_slug) or force_update:
            author_name = ""
            if self.author:
                author_name = self.author.name

            if not data:
                logger.warn(f"Checking openlibrary for {self.title}")
                if self.openlibrary_id and force_update:
                    data = lookup_book_from_openlibrary(
                        str(self.openlibrary_id)
                    )
                else:
                    data = lookup_book_from_openlibrary(
                        str(self.title), author_name
                    )

            if not data:
                if self.locg_slug:
                    logger.warn(
                        f"Checking LOCG for {self.title} with slug {self.locg_slug}"
                    )
                    data = lookup_comic_by_locg_slug(str(self.locg_slug))
                else:
                    logger.warn(f"Checking LOCG for {self.title}")
                    data = lookup_comic_from_locg(str(self.title))

            if not data and COMICVINE_API_KEY:
                logger.warn(f"Checking ComicVine for {self.title}")
                cv_client = ComicVineClient(api_key=COMICVINE_API_KEY)
                data = lookup_comic_from_comicvine(str(self.title))

            if not data:
                logger.warn(f"Book not found in any sources: {self.title}")
                return

            # We can discard the author name from OL for now, we'll lookup details below
            data.pop("ol_author_name", "")
            if data.get("ol_author_id"):
                self.fix_authors_metadata(data.pop("ol_author_id", ""))
            if data.get("locg_writer_slug"):
                self.get_author_from_locg(data.pop("locg_writer_slug", ""))

            ol_title = data.get("title", "")
            data.pop("ol_author_id", "")

            # Kick out a little warning if we're about to change KoReader's title
            if (
                fuzz.ratio(ol_title.lower(), str(self.title).lower()) < 80
                and not force_update
            ):
                logger.warn(
                    f"OL and KoReader disagree on this book title {self.title} != {ol_title}, check manually"
                )
                self.openlibrary_id = data.get("openlibrary_id")
                self.save(update_fields=["openlibrary_id"])
                return

            # If we don't know pages, don't overwrite existing with None
            if "pages" in data.keys() and data.get("pages") == None:
                data.pop("pages")

            if (
                not isinstance(data.get("pages"), int)
                and "pages" in data.keys()
            ):
                logger.info(
                    f"Pages for {self} from OL expected to be int, but got {data.get('pages')}"
                )
                data.pop("pages")

            # Pop this, so we can look it up later
            cover_url = data.pop("cover_url", "")

            subject_key_list = data.pop("subject_key_list", "")

            # Fun trick for updating all fields at once
            Book.objects.filter(pk=self.id).update(**data)
            self.refresh_from_db()

            if subject_key_list:
                self.genre.add(*subject_key_list)

            if cover_url:
                r = requests.get(cover_url)
                if r.status_code == 200:
                    fname = f"{self.title}_{self.uuid}.jpg"
                    self.cover.save(fname, ContentFile(r.content), save=True)

            if self.pages:
                self.run_time_seconds = int(self.pages) * int(
                    self.AVG_PAGE_READING_SECONDS
                )

            self.save()

    def fix_authors_metadata(self, openlibrary_author_id):
        author = Author.objects.filter(
            openlibrary_id=openlibrary_author_id
        ).first()
        if not author:
            data = lookup_author_from_openlibrary(openlibrary_author_id)
            author_image_url = data.pop("author_headshot_url", None)

            author = Author.objects.create(**data)

            if author_image_url:
                r = requests.get(author_image_url)
                if r.status_code == 200:
                    fname = f"{author.name}_{author.uuid}.jpg"
                    author.headshot.save(
                        fname, ContentFile(r.content), save=True
                    )
        self.authors.add(author)

    def get_author_from_locg(self, locg_slug):
        writer = lookup_comic_writer_by_locg_slug(locg_slug)

        author, created = Author.objects.get_or_create(
            name=writer["name"], locg_slug=writer["locg_slug"]
        )
        if (created or not author.headshot) and writer["photo_url"]:
            r = requests.get(writer["photo_url"])
            if r.status_code == 200:
                fname = f"{author.name}_{author.uuid}.jpg"
                author.headshot.save(fname, ContentFile(r.content), save=True)
        self.authors.add(author)

    def page_data_for_user(
        self, user_id: int, convert_timestamps: bool = True
    ) -> dict:
        scrobbles = self.scrobble_set.filter(user=user_id)

        pages = {}
        for scrobble in scrobbles:
            if scrobble.logdata.page_data:
                for page, data in scrobble.logdata.page_data.items():
                    if convert_timestamps:
                        data["start_ts"] = datetime.fromtimestamp(
                            data["start_ts"]
                        )
                        data["end_ts"] = datetime.fromtimestamp(data["end_ts"])
                    pages[page] = data
        sorted_pages = OrderedDict(
            sorted(pages.items(), key=lambda x: x[1]["start_ts"])
        )

        return sorted_pages

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
            progress = int((last_scrobble.last_page_read / self.pages) * 100)
        return progress

    @classmethod
    def find_or_create(cls, lookup_id: str, author: str = "") -> "Book":
        book = cls.objects.filter(openlibrary_id=lookup_id).first()

        if not book:
            data = lookup_book_from_openlibrary(lookup_id, author)

            if not data:
                logger.error(
                    f"No book found on openlibrary, or in our database for {lookup_id}"
                )
                return book

            book, book_created = cls.objects.get_or_create(isbn=data["isbn"])
            if book_created:
                book.fix_metadata(data=data)

        return book


class Page(TimeStampedModel):
    """DEPRECATED, we need to migrate pages into page_data on scrobbles and move on"""

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    number = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
