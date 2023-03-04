import logging
import time
from datetime import datetime, timedelta

import pylast
import pytz
from django.conf import settings
from django.utils import timezone
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
        lastfm_scrobbles = self.get_last_scrobbles(time_from=last_processed)

        for lfm_scrobble in lastfm_scrobbles:
            timestamp = lfm_scrobble.pop('timestamp')

            artist = get_or_create_artist(lfm_scrobble.pop('artist'))
            album = get_or_create_album(lfm_scrobble.pop('album'), artist)

            lfm_scrobble['artist'] = artist
            lfm_scrobble['album'] = album
            track = get_or_create_track(**lfm_scrobble)

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
            seconds_eariler = timestamp - timedelta(seconds=20)
            seconds_later = timestamp + timedelta(seconds=20)
            existing = Scrobble.objects.filter(
                created__gte=seconds_eariler,
                created__lte=seconds_later,
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

    def get_last_scrobbles(self, time_from=None, time_to=None):
        """Given a user, Last.fm api key, and secret key, grab a list of scrobbled
        tracks"""
        lfm_params = {}
        scrobbles = []
        if time_from:
            lfm_params["time_from"] = int(time_from.timestamp())
        if time_to:
            lfm_params["time_to"] = int(time_to.timestamp())

        # if not time_from and not time_to:
        lfm_params['limit'] = None

        found_scrobbles = self.user.get_recent_tracks(**lfm_params)
        # TOOD spin this out into a celery task over certain threshold of found scrobbles?

        for scrobble in found_scrobbles:
            run_time = None
            run_time_ticks = None
            mbid = None
            artist = None

            try:
                run_time_ticks = scrobble.track.get_duration()
                run_time = int(run_time_ticks / 1000)
                mbid = scrobble.track.get_mbid()
                artist = scrobble.track.get_artist().name
            except pylast.MalformedResponseError as e:
                logger.warn(e)
            except pylast.WSError as e:
                logger.warn(
                    "LastFM barfed trying to get the track for {scrobble.track}"
                )

            if not artist:
                logger.warn(f"Silly LastFM, no artist found for {scrobble}")
                continue

            timestamp = datetime.utcfromtimestamp(
                int(scrobble.timestamp)
            ).replace(tzinfo=pytz.utc)

            logger.info(f"{artist},{scrobble.track.title},{timestamp}")
            scrobbles.append(
                {
                    "artist": artist,
                    "album": scrobble.album,
                    "title": scrobble.track.title,
                    "mbid": mbid,
                    "run_time": run_time,
                    "run_time_ticks": run_time_ticks,
                    "timestamp": timestamp,
                }
            )
        return scrobbles
