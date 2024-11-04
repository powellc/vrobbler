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

from vrobbler.apps.scrobbles.utils import timestamp_user_tz_to_utc

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

    rockbox_info = ""
    for row_num, row in enumerate(rows):
        if row_num in [0, 1, 2]:
            if "Rockbox" in row[0]:
                source = "Rockbox"
            rockbox_info += row[0] + "\n"
            continue
        if len(row) > 8:
            logger.warning(
                "Improper row length during Audioscrobbler import",
                extra={"row": row},
            )
            continue

        track = get_or_create_track(
            {
                "title": row[AsTsvColumn["TRACK_NAME"].value],
                "mbid": row[AsTsvColumn["MB_ID"].value],
                "artist_name": row[AsTsvColumn["ARTIST_NAME"].value],
                "album_name": row[AsTsvColumn["ALBUM_NAME"].value],
                "run_time_seconds": int(
                    row[AsTsvColumn["RUN_TIME_SECONDS"].value]
                ),
            },
            {
                "TRACK_MB_ID": "mbid",
                "TRACK_TITLE": "track_title",
                "ALBUM_NAME": "album_name",
                "ARTIST_NAME": "artist_name",
                "RUN_TIME": "run_time_seconds",
            },
        )
        if not track:
            logger.info(f"Skipping track {track} because not found")
            continue

        # TODO Set all this up as constants
        if row[AsTsvColumn["COMPLETE"].value] == "S":
            logger.info(f"Skipping track {track} because not finished")
            continue

        timestamp = timestamp_user_tz_to_utc(
            int(row[AsTsvColumn["TIMESTAMP"].value]), user_tz
        )

        new_scrobble = Scrobble(
            user_id=user_id,
            timestamp=timestamp,
            source=source,
            log={"rockbox_info": rockbox_info},
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
