from django.core.management.base import BaseCommand
from scrobbles.models import Scrobble


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Actually migrate data",
        )

    def handle(self, *args, **options):
        dry_run = True
        if options["commit"]:
            dry_run = False

        scrobbles_with_logs = (
            Scrobble.objects.filter(scrobble_log__isnull=False)
            .exclude(scrobble_log="")
            .exclude(scrobble_log="\n")
        )
        updated_scrobble_count = 0

        for scrobble in scrobbles_with_logs:
            if "\n" in scrobble.scrobble_log:
                lines = scrobble.scrobble_log.split("\n")
            else:
                lines = [scrobble.scrobble_log]

            old_data = {}
            for line_num, line in enumerate(lines):
                if line_num == 0 or line == "":
                    continue
                old_data[str(line_num)] = line

            if old_data:
                scrobble.scrobble_log = {"legacy_data": old_data}
                updated_scrobble_count += 1

                if not dry_run:
                    scrobble.save(update_fields=["scrobble_log"])
                else:
                    print(
                        f"Scrobble {scrobble} scrobble_log updated to {old_data}"
                    )

        print(f"Migrated scrobble logs for {updated_scrobble_count} scrobbles")
