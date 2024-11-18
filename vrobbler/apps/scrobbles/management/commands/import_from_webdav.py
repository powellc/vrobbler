from django.core.management.base import BaseCommand
from vrobbler.apps.scrobbles.utils import import_from_webdav_for_all_users


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--restart",
            action="store_true",
            help="Restart failed imports",
        )

    def handle(self, *args, **options):
        restart = False
        if options["restart"]:
            restart = True
        count = import_from_webdav_for_all_users(restart=restart)
        print(f"Started {count} WeDAV imports")
