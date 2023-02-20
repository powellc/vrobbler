import csv
import logging
from datetime import datetime

import pytz
from scrobbles.models import Scrobble
from music.utils import (
    get_or_create_album,
    get_or_create_artist,
    get_or_create_track,
)

logger = logging.getLogger(__name__)


def process_audioscrobbler_tsv_file(file_path, user_id, user_tz=None):
    """Takes a path to a file of TSV data and imports it as past scrobbles"""
    new_scrobbles = []
    if not user_tz:
        user_tz = pytz.utc

    with open(file_path) as infile:
        source = 'Audioscrobbler File'
        rows = csv.reader(infile, delimiter="\t")

        source_id = ""
        for row_num, row in enumerate(rows):
            if row_num in [0, 1, 2]:
                if "Rockbox" in row[0]:
                    source = "Rockbox"
                source_id += row[0] + "\n"
                continue
            if len(row) > 8:
                logger.warning(
                    'Improper row length during Audioscrobbler import',
                    extra={'row': row},
                )
                continue
            artist = get_or_create_artist(row[0])
            album = get_or_create_album(row[1], artist)

            track = get_or_create_track(
                title=row[2],
                mbid=row[7],
                artist=artist,
                album=album,
                run_time=row[4],
                run_time_ticks=int(row[4]) * 1000,
            )

            timestamp = (
                datetime.utcfromtimestamp(int(row[6]))
                .replace(tzinfo=user_tz)
                .astimezone(pytz.utc)
            )

            new_scrobble = Scrobble(
                user_id=user_id,
                timestamp=timestamp,
                source=source,
                source_id=source_id,
                track=track,
                played_to_completion=True,
                in_progress=False,
            )
            existing = Scrobble.objects.filter(
                timestamp=timestamp, track=track
            ).first()
            if existing:
                logger.debug(f"Skipping existing scrobble {new_scrobble}")
                continue
            logger.debug(f"Queued scrobble {new_scrobble} for creation")
            new_scrobbles.append(new_scrobble)

        created = Scrobble.objects.bulk_create(new_scrobbles)
        logger.info(
            f"Created {len(created)} scrobbles",
            extra={'created_scrobbles': created},
        )
        return created
