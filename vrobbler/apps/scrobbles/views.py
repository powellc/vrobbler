import json
import logging
from datetime import datetime, timedelta

from dateutil.parser import parse
from django.conf import settings
from django.db.models.fields import timezone
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView
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
from videos.models import Video

from vrobbler.apps.music.constants import JELLYFIN_POST_KEYS as KEYS

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
        last_three_minutes = timezone.now() - timedelta(minutes=3)
        # Find scrobbles from the last 10 minutes
        data['now_playing_list'] = Scrobble.objects.filter(
            in_progress=True,
            timestamp__gte=last_three_minutes,
            timestamp__lte=now,
        )
        return data

    def get_queryset(self):
        return Scrobble.objects.filter(in_progress=False).order_by(
            '-timestamp'
        )


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

        track_dict = {
            "title": data_dict.get("Name", ""),
            "musicbrainz_id": data_dict.get(KEYS["TRACK_MB_ID"], None),
            "run_time_ticks": data_dict.get(KEYS["RUN_TIME_TICKS"], None),
            "run_time": data_dict.get(KEYS["RUN_TIME"], None),
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
        "playback_position_ticks": data_dict.get("PlaybackPositionTicks"),
        "playback_position": data_dict.get("PlaybackPosition"),
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
        "musicbrainz_id": data_dict.get("musicbrainz_track_id"),
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
        scrobble = Scrobble.create_or_update_for_track(
            track, request.user.id, mopidy_data
        )

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {'scrobble_id': scrobble.id}, status=status.HTTP_201_CREATED
    )
