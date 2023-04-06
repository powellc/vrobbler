from django.core.management.base import BaseCommand, no_translations
from vrobbler.apps.scrobbles.utils import import_lastfm_for_all_users


class Command(BaseCommand):
    def handle(self, *args, **options):
        import_lastfm_for_all_users()
