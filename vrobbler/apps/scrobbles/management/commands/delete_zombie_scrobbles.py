from django.core.management.base import BaseCommand, no_translations
from vrobbler.apps.scrobbles.utils import delete_zombie_scrobbles


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete poll instead of closing it",
        )

    def handle(self, *args, **options):
        dry_run = True
        if options["delete"]:
            dry_run = False
        scrobbles_found = delete_zombie_scrobbles(dry_run)

        if not scrobbles_found:
            print(f"No zombie scrobbles found to delete")
            return

        if not dry_run:
            print(f"Deleted {scrobbles_found} zombie scrobbles")
            return

        print(
            f"Found {scrobbles_found} zombie scrobbles, use --delete to remove them"
        )
