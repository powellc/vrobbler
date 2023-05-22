import codecs
import csv
import logging
from datetime import datetime

import pytz
import requests
from music.utils import (
    get_or_create_album,
    get_or_create_artist,
    get_or_create_track,
)
from scrobbles.constants import AsTsvColumn
from scrobbles.models import Scrobble

logger = logging.getLogger(__name__)


def process_audioscrobbler_tsv_file(file_path, user_id, user_tz=None):
    """Takes a path to a file of TSV data and imports it as past scrobbles"""
    new_scrobbles = []
    if not user_tz:
        user_tz = pytz.utc

    is_os_file = "https://" not in file_path

    if not is_os_file:
        r = requests.get(file_path)
        tsv_data = codecs.iterdecode(r.iter_lines(), "utf-8")
    else:
        tsv_data = open(file_path)

    source = "Audioscrobbler File"
    rows = csv.reader(tsv_data, delimiter="\t")

    source_id = ""
    for row_num, row in enumerate(rows):
        if row_num in [0, 1, 2]:
            if "Rockbox" in row[0]:
                source = "Rockbox"
            source_id += row[0] + "\n"
            continue
        if len(row) > 8:
            logger.warning(
                "Improper row length during Audioscrobbler import",
                extra={"row": row},
            )
            continue

        artist = get_or_create_artist(row[AsTsvColumn["ARTIST_NAME"].value])
        album = get_or_create_album(
            row[AsTsvColumn["ALBUM_NAME"].value], artist
        )

        track = get_or_create_track(
            title=row[AsTsvColumn["TRACK_NAME"].value],
            mbid=row[AsTsvColumn["MB_ID"].value],
            artist=artist,
            album=album,
            run_time_seconds=int(row[AsTsvColumn["RUN_TIME_SECONDS"].value]),
        )
        if row[AsTsvColumn["COMPLETE"].value] == "S":
            logger.info(
                f"Skipping track {track} by {artist} because not finished"
            )
            continue

        timestamp = (
            datetime.utcfromtimestamp(int(row[AsTsvColumn["TIMESTAMP"].value]))
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
            media_type=Scrobble.MediaType.TRACK,
        )
        existing = Scrobble.objects.filter(
            timestamp=timestamp, track=track
        ).first()
        if existing:
            logger.debug(f"Skipping existing scrobble {new_scrobble}")
            continue
        logger.debug(f"Queued scrobble {new_scrobble} for creation")
        new_scrobbles.append(new_scrobble)

    if is_os_file:
        tsv_data.close()

    created = Scrobble.objects.bulk_create(new_scrobbles)
    logger.info(
        f"Created {len(created)} scrobbles",
        extra={"created_scrobbles": created},
    )
    return created
