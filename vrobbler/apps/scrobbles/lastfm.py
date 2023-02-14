import logging
import time
from datetime import datetime, timedelta

import pylast
import pytz
from django.conf import settings
from music.utils import (
    get_or_create_album,
    get_or_create_artist,
    get_or_create_track,
)

logger = logging.getLogger(__name__)

PYLAST_ERRORS = tuple(
    getattr(pylast, exc_name)
    for exc_name in (
        "ScrobblingError",
        "NetworkError",
        "MalformedResponseError",
        "WSError",
    )
    if hasattr(pylast, exc_name)
)


class LastFM:
    def __init__(self, user):
        try:
            self.client = pylast.LastFMNetwork(
                api_key=getattr(settings, "LASTFM_API_KEY"),
                api_secret=getattr(settings, "LASTFM_SECRET_KEY"),
                username=user.profile.lastfm_username,
                password_hash=pylast.md5(user.profile.lastfm_password),
            )
            self.user = self.client.get_user(user.profile.lastfm_username)
            self.vrobbler_user = user
        except PYLAST_ERRORS as e:
            logger.error(f"Error during Last.fm setup: {e}")

    def import_from_lastfm(self, last_processed=None):
        """Given a last processed time, import all scrobbles from LastFM since then"""
        from scrobbles.models import Scrobble

        new_scrobbles = []
        source = "Last.fm"
        source_id = ""
        latest_scrobbles = self.get_last_scrobbles(time_from=last_processed)

        for scrobble in latest_scrobbles:
            timestamp = scrobble.pop('timestamp')

            artist = get_or_create_artist(scrobble.pop('artist'))
            album = get_or_create_album(scrobble.pop('album'), artist)

            scrobble['artist'] = artist
            scrobble['album'] = album
            track = get_or_create_track(**scrobble)

            new_scrobble = Scrobble(
                user=self.vrobbler_user,
                timestamp=timestamp,
                source=source,
                source_id=source_id,
                track=track,
                played_to_completion=True,
                in_progress=False,
            )
            # Vrobbler scrobbles on finish, LastFM scrobbles on start
            ten_seconds_eariler = timestamp - timedelta(seconds=15)
            ten_seconds_later = timestamp + timedelta(seconds=15)
            existing = Scrobble.objects.filter(
                created__gte=ten_seconds_eariler,
                created__lte=ten_seconds_later,
                track=track,
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

    @staticmethod
    def undo_lastfm_import(process_log, dryrun=True):
        """Given a newline separated list of scrobbles, delete them"""
        from scrobbles.models import Scrobble

        if not process_log:
            logger.warning("No lines in process log found to undo")
            return

        for line in process_log.split('\n'):
            scrobble_id = line.split("\t")[0]
            scrobble = Scrobble.objects.filter(id=scrobble_id).first()
            if not scrobble:
                logger.warning(
                    f"Could not find scrobble {scrobble_id} to undo"
                )
                continue
            logger.info(f"Removing scrobble {scrobble_id}")
            if not dryrun:
                scrobble.delete()

    def get_last_scrobbles(self, time_from=None, time_to=None):
        """Given a user, Last.fm api key, and secret key, grab a list of scrobbled
        tracks"""
        scrobbles = []
        if time_from:
            time_from = int(time_from.timestamp())
        if time_to:
            time_to = int(time_to.timestamp())

        if not time_from and not time_to:
            found_scrobbles = self.user.get_recent_tracks(limit=None)
        else:
            found_scrobbles = self.user.get_recent_tracks(
                time_from=time_from, time_to=time_to
            )
        for scrobble in found_scrobbles:
            run_time_ticks = scrobble.track.get_duration()
            run_time = run_time_ticks / 1000
            scrobbles.append(
                {
                    "artist": scrobble.track.get_artist().name,
                    "album": scrobble.album,
                    "title": scrobble.track.title,
                    "mbid": scrobble.track.get_mbid(),
                    "run_time": int(run_time),
                    "run_time_ticks": run_time_ticks,
                    "timestamp": datetime.utcfromtimestamp(
                        int(scrobble.timestamp)
                    ).replace(tzinfo=pytz.utc),
                }
            )
        return scrobbles
