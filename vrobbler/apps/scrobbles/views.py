import json
import logging
from datetime import datetime, timedelta

from dateutil.parser import parse
from django.conf import settings
from django.db.models.fields import timezone
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView
from music.constants import JELLYFIN_POST_KEYS as KEYS
from music.models import Track
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from scrobbles.constants import (
    JELLYFIN_AUDIO_ITEM_TYPES,
    JELLYFIN_VIDEO_ITEM_TYPES,
)
from scrobbles.models import Scrobble
from scrobbles.serializers import ScrobbleSerializer
from scrobbles.utils import convert_to_seconds
from videos.models import Video
from vrobbler.apps.music.aggregators import (
    scrobble_counts,
    top_artists,
    top_tracks,
    week_of_scrobbles,
)

logger = logging.getLogger(__name__)

TRUTHY_VALUES = [
    'true',
    '1',
    't',
    'y',
    'yes',
    'yeah',
    'yup',
    'certainly',
    'uh-huh',
]


class RecentScrobbleList(ListView):
    model = Scrobble

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        now = timezone.now()
        last_eight_minutes = timezone.now() - timedelta(minutes=8)
        # Find scrobbles from the last 10 minutes
        data['now_playing_list'] = Scrobble.objects.filter(
            in_progress=True,
            is_paused=False,
            timestamp__gte=last_eight_minutes,
            timestamp__lte=now,
        )
        data['video_scrobble_list'] = Scrobble.objects.filter(
            video__isnull=False, in_progress=False
        ).order_by('-timestamp')[:10]
        data['top_daily_tracks'] = top_tracks()
        data['top_weekly_tracks'] = top_tracks(filter='week')
        data['top_monthly_tracks'] = top_tracks(filter='month')

        data['top_daily_artists'] = top_artists()
        data['top_weekly_artists'] = top_artists(filter='week')
        data['top_monthly_artists'] = top_artists(filter='month')

        data["weekly_data"] = week_of_scrobbles()
        data['counts'] = scrobble_counts()
        return data

    def get_queryset(self):
        return Scrobble.objects.filter(
            track__isnull=False, in_progress=False
        ).order_by('-timestamp')[:15]


@csrf_exempt
@api_view(['GET'])
def scrobble_endpoint(request):
    """List all Scrobbles, or create a new Scrobble"""
    scrobble = Scrobble.objects.all()
    serializer = ScrobbleSerializer(scrobble, many=True)
    return Response(serializer.data)


@csrf_exempt
@api_view(['POST'])
def jellyfin_websocket(request):
    data_dict = request.data

    # For making things easier to build new input processors
    if getattr(settings, "DUMP_REQUEST_DATA", False):
        json_data = json.dumps(data_dict, indent=4)
        logger.debug(f"{json_data}")

    media_type = data_dict.get("ItemType", "")

    track = None
    video = None
    if media_type in JELLYFIN_AUDIO_ITEM_TYPES:
        if not data_dict.get("Provider_musicbrainztrack", None):
            logger.error(
                "No MBrainz Track ID received. This is likely because all metadata is bad, not scrobbling"
            )
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        artist_dict = {
            'name': data_dict.get(KEYS["ARTIST_NAME"], None),
            'musicbrainz_id': data_dict.get(KEYS["ARTIST_MB_ID"], None),
        }

        album_dict = {
            "name": data_dict.get(KEYS["ALBUM_NAME"], None),
            "year": data_dict.get(KEYS["YEAR"], ""),
            "musicbrainz_id": data_dict.get(KEYS['ALBUM_MB_ID']),
            "musicbrainz_releasegroup_id": data_dict.get(
                KEYS["RELEASEGROUP_MB_ID"]
            ),
            "musicbrainz_albumartist_id": data_dict.get(KEYS["ARTIST_MB_ID"]),
        }

        # Convert ticks from Jellyfin from microseconds to nanoseconds
        # Ain't nobody got time for nanoseconds
        track_dict = {
            "title": data_dict.get("Name", ""),
            "run_time_ticks": data_dict.get(KEYS["RUN_TIME_TICKS"], None)
            // 10000,
            "run_time": convert_to_seconds(
                data_dict.get(KEYS["RUN_TIME"], None)
            ),
        }
        track = Track.find_or_create(artist_dict, album_dict, track_dict)

    if media_type in JELLYFIN_VIDEO_ITEM_TYPES:
        if not data_dict.get("Provider_imdb", None):
            logger.error(
                "No IMDB ID received. This is likely because all metadata is bad, not scrobbling"
            )
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        video = Video.find_or_create(data_dict)

    # Now we run off a scrobble
    jellyfin_data = {
        "user_id": request.user.id,
        "timestamp": parse(data_dict.get("UtcTimestamp")),
        "playback_position_ticks": data_dict.get("PlaybackPositionTicks")
        // 10000,
        "playback_position": convert_to_seconds(
            data_dict.get("PlaybackPosition")
        ),
        "source": "Jellyfin",
        "source_id": data_dict.get('MediaSourceId'),
        "is_paused": data_dict.get("IsPaused") in TRUTHY_VALUES,
    }

    scrobble = None
    if video:
        scrobble = Scrobble.create_or_update_for_video(
            video, request.user.id, jellyfin_data
        )
    if track:
        # Prefer Mopidy MD IDs to Jellyfin, so skip if we already have one
        if not track.musicbrainz_id:
            track.musicbrainz_id = data_dict.get(KEYS["TRACK_MB_ID"], None)
            track.save()
        scrobble = Scrobble.create_or_update_for_track(
            track, request.user.id, jellyfin_data
        )

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {'scrobble_id': scrobble.id}, status=status.HTTP_201_CREATED
    )


@csrf_exempt
@api_view(['POST'])
def mopidy_websocket(request):
    data_dict = json.loads(request.data)

    # For making things easier to build new input processors
    if getattr(settings, "DUMP_REQUEST_DATA", False):
        json_data = json.dumps(data_dict, indent=4)

    artist_dict = {
        "name": data_dict.get("artist", None),
        "musicbrainz_id": data_dict.get("musicbrainz_artist_id", None),
    }

    album_dict = {
        "name": data_dict.get("album"),
        "musicbrainz_id": data_dict.get("musicbrainz_album_id"),
    }

    track_dict = {
        "title": data_dict.get("name"),
        "run_time_ticks": data_dict.get("run_time_ticks"),
        "run_time": data_dict.get("run_time"),
    }

    track = Track.find_or_create(artist_dict, album_dict, track_dict)

    # Now we run off a scrobble
    mopidy_data = {
        "user_id": request.user.id,
        "timestamp": timezone.now(),
        "source": "Mopidy",
        "status": data_dict.get("status"),
    }

    scrobble = None
    if track:
        # Jellyfin MB ids suck, so always overwrite with Mopidy if they're offering
        track.musicbrainz_id = data_dict.get("musicbrainz_track_id")
        track.save()
        scrobble = Scrobble.create_or_update_for_track(
            track, request.user.id, mopidy_data
        )

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {'scrobble_id': scrobble.id}, status=status.HTTP_201_CREATED
    )
