from books.models import Book
from django.core.management.base import BaseCommand
from scrobbles.models import ScrobbledPage


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Actually populate data",
        )

    def handle(self, *args, **options):
        dry_run = True
        if options["commit"]:
            dry_run = False

        pages_to_create = []
        associated_scrobble = None
        last_scrobble = None
        for book in Book.objects.all():
            for page in book.page_set.all().order_by("number"):
                notes = ""
                last_scrobble = associated_scrobble
                if (
                    not associated_scrobble
                    or page.number > associated_scrobble.book_pages_read
                ):
                    associated_scrobble = page.user.scrobble_set.filter(
                        book=page.book,
                        timestamp__gte=page.start_time,
                        timestamp__lte=page.end_time,
                    ).first()

                if (
                    last_scrobble
                    and not associated_scrobble
                    and page.number > last_scrobble.book_pages_read
                ):
                    associated_scrobble = last_scrobble
                    notes = f"Extrapolated reading from scrobble {associated_scrobble.id}"

                pages_to_create.append(
                    ScrobbledPage(
                        scrobble=associated_scrobble,
                        number=page.number,
                        start_time=page.start_time,
                        end_time=page.end_time,
                        duration_seconds=page.duration_seconds,
                        notes=notes,
                    )
                )

        pages_to_move_len = len(pages_to_create)
        if dry_run:
            print(
                f"Found {pages_to_move_len} to migrate. Use --commit to move them"
            )
            return

        ScrobbledPage.objects.bulk_create(pages_to_create)
        print(f"Migrated {pages_to_move_len} generic pages to scrobbled pages")
