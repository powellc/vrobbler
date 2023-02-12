import csv
import logging
from datetime import datetime

import pytz
from music.models import Album, Artist, Track
from scrobbles.models import Scrobble

from vrobbler.apps.scrobbles.musicbrainz import (
    lookup_album_dict_from_mb,
    lookup_artist_id_from_mb,
)

logger = logging.getLogger(__name__)


def process_audioscrobbler_tsv_file(file_path, user_tz=None):
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
                artist.musicbrainz_id = lookup_artist_id_from_mb(artist.name)
                artist.save(update_fields=["musicbrainz_id"])

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
                album_dict = lookup_album_dict_from_mb(
                    album.name, artist_name=artist.name
                )
                album.year = album_dict["year"]
                album.musicbrainz_id = album_dict["mb_id"]
                album.musicbrainz_releasegroup_id = album_dict["mb_group_id"]
                album.musicbrainz_albumartist_id = artist.musicbrainz_id
                album.save(
                    update_fields=[
                        "year",
                        "musicbrainz_id",
                        "musicbrainz_releasegroup_id",
                        "musicbrainz_albumartist_id",
                    ]
                )
                album.artists.add(artist)
                album.fetch_artwork()

            track, track_created = Track.objects.get_or_create(
                title=row[2],
                artist=artist,
                album=album,
                musicbrainz_id=row[7],
            )

            if track_created:
                track.run_time = int(row[4])
                track.run_time_ticks = int(row[4]) * 1000
                track.save()

            timestamp = (
                datetime.utcfromtimestamp(int(row[6]))
                .replace(tzinfo=user_tz)
                .astimezone(pytz.utc)
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

    for line in process_log.split('\n'):
        scrobble_id = line.split("\t")[0]
        scrobble = Scrobble.objects.filter(id=scrobble_id).first()
        if not scrobble:
            logger.warning(f"Could not find scrobble {scrobble_id} to undo")
            continue
        logger.info(f"Removing scrobble {scrobble_id}")
        if not dryrun:
            scrobble.delete()
