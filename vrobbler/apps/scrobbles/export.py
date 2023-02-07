import csv
import tempfile
from scrobbles.models import Scrobble

from django.db.models import Q


def export_scrobbles(start_date=None, end_date=None, format="AS"):
    start_query = Q()
    end_query = Q()
    if start_date:
        start_query = Q(timestamp__gte=start_date)
    if start_date:
        end_query = Q(timestamp__lte=end_date)

    scrobble_qs = Scrobble.objects.filter(
        start_query, end_query, track__isnull=False
    )
    headers = []
    extension = 'tsv'
    delimiter = '\t'

    if format == "as":
        headers = [
            ['#AUDIOSCROBBLER/1.1'],
            ['#TZ/UTC'],
            ['#CLIENT/Vrobbler 1.0.0'],
        ]

    if format == "csv":
        delimiter = ','
        extension = 'csv'
        headers = [
            [
                "artists",
                "album",
                "title",
                "track_number",
                "run_time",
                "rating",
                "timestamp",
                "musicbrainz_id",
            ]
        ]

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as outfile:
        writer = csv.writer(outfile, delimiter=delimiter)
        for row in headers:
            writer.writerow(row)

        for scrobble in scrobble_qs:
            track = scrobble.track
            track_number = 0  # TODO Add track number
            track_rating = "S"  # TODO implement ratings?
            track_artist = track.artist or track.album.primary_artist
            row = [
                track_artist,
                track.album.name,
                track.title,
                track_number,
                track.run_time,
                track_rating,
                scrobble.timestamp.strftime('%s'),
                track.musicbrainz_id,
            ]
            writer.writerow(row)
        return outfile.name, extension
