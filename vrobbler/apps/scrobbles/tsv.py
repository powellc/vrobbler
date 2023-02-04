import csv
import logging
from datetime import datetime

import pytz
from music.models import Album, Artist, Track
from scrobbles.models import Scrobble

logger = logging.getLogger(__name__)


def process_audioscrobbler_tsv_file(file_path):
    """Takes a path to a file of TSV data and imports it as past scrobbles"""
    new_scrobbles = []

    with open(file_path) as infile:
        source = 'Audioscrobbler File'
        rows = csv.reader(infile, delimiter="\t")

        source_id = ""
        for row_num, row in enumerate(rows):
            if row_num in [0, 1, 2]:
                source_id += row[0] + "\n"
                continue
            if len(row) > 8:
                logger.warning(
                    'Improper row length during Audioscrobbler import',
                    extra={'row': row},
                )
                continue
            artist, artist_created = Artist.objects.get_or_create(name=row[0])
            if artist_created:
                logger.debug(f"Created artist {artist}")
            else:
                logger.debug(f"Found artist {artist}")

            album = None
            album_created = False
            albums = Album.objects.filter(name=row[1])
            if albums.count() == 1:
                album = albums.first()
            else:
                for potential_album in albums:
                    if artist in album.artist_set.all():
                        album = potential_album
            if not album:
                album_created = True
                album = Album.objects.create(name=row[1])
                album.save()
                album.artists.add(artist)

            if album_created:
                logger.debug(f"Created album {album}")
            else:
                logger.debug(f"Found album {album}")

            track, track_created = Track.objects.get_or_create(
                title=row[2],
                artist=artist,
                album=album,
            )

            if track_created:
                logger.debug(f"Created track {track}")
            else:
                logger.debug(f"Found track {track}")

            if track_created:
                track.musicbrainz_id = row[7]
                track.save()

            timestamp = datetime.utcfromtimestamp(int(row[6])).replace(
                tzinfo=pytz.utc
            )
            source = 'Audioscrobbler File'

            new_scrobble = Scrobble(
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


def undo_audioscrobbler_tsv_import(process_log, dryrun=True):
    """Accepts the log from a TSV import and removes the scrobbles"""
    if not process_log:
        logger.warning("No lines in process log found to undo")
        return

    for line_num, line in enumerate(process_log.split('\n')):
        if line_num == 0:
            continue
        scrobble_id = line.split("\t")[0]
        scrobble = Scrobble.objects.filter(id=scrobble_id).first()
        if not scrobble:
            logger.warning(f"Could not find scrobble {scrobble_id} to undo")
            continue
        logger.info(f"Removing scrobble {scrobble_id}")
        if not dryrun:
            scrobble.delete()
