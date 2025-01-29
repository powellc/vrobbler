from django.core.management.base import BaseCommand
from vrobbler.apps.boardgames.sources.lichess import (
    import_chess_games_for_all_users,
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        count = len(import_chess_games_for_all_users())
        print(f"Imported {count} Lichess games")
