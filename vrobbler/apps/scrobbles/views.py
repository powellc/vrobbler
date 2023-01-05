import json
import logging
from datetime import datetime, timedelta

from dateutil.parser import parse
from django.conf import settings
from django.db.models.fields import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from scrobbles.models import Scrobble
from scrobbles.serializers import ScrobbleSerializer
from videos.models import Series, Video
from vrobbler.settings import DELETE_STALE_SCROBBLES

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
    media_type = data_dict["ItemType"]
    # Check if it's a TV Episode
    video_dict = {
        "title": data_dict["Name"],
        "imdb_id": data_dict["Provider_imdb"],
        "video_type": Video.VideoType.MOVIE,
        "year": data_dict["Year"],
    }
    if media_type == 'Episode':
        series_name = data_dict["SeriesName"]
        series, series_created = Series.objects.get_or_create(name=series_name)

        video_dict['video_type'] = Video.VideoType.TV_EPISODE
        video_dict["tv_series_id"] = series.id
        video_dict["episode_number"] = data_dict["EpisodeNumber"]
        video_dict["season_number"] = data_dict["SeasonNumber"]
        video_dict["tvdb_id"] = data_dict.get("Provider_tvdb", None)
        video_dict["tvrage_id"] = data_dict.get("Provider_tvrage", None)

    video, video_created = Video.objects.get_or_create(**video_dict)

    if video_created:
        video.overview = data_dict["Overview"]
        video.tagline = data_dict["Tagline"]
        video.run_time_ticks = data_dict["RunTimeTicks"]
        video.run_time = data_dict["RunTime"]
        video.save()

    # Now we run off a scrobble
    timestamp = parse(data_dict["UtcTimestamp"])
    scrobble_dict = {
        'video_id': video.id,
        'user_id': request.user.id,
        'in_progress': True,
    }

    existing_finished_scrobble = (
        Scrobble.objects.filter(
            video=video, user_id=request.user.id, in_progress=False
        )
        .order_by('-modified')
        .first()
    )
    existing_in_progress_scrobble = (
        Scrobble.objects.filter(
            video=video, user_id=request.user.id, in_progress=True
        )
        .order_by('-modified')
        .first()
    )

    minutes_from_now = timezone.now() + timedelta(minutes=15)
    a_day_from_now = timezone.now() + timedelta(days=1)

    if (
        existing_finished_scrobble
        and existing_finished_scrobble.modified < minutes_from_now
    ):
        logger.info(
            'Found a scrobble for this video less than 15 minutes ago, holding off scrobbling again'
        )
        return Response(video_dict, status=status.HTTP_204_NO_CONTENT)

    existing_scrobble_more_than_a_day_old = (
        existing_in_progress_scrobble
        and existing_in_progress_scrobble.modified > a_day_from_now
    )
    delete_stale_scrobbles = getattr(settings, "DELETE_STALE_SCROBBLES", True)

    # Check if found in progress scrobble is more than a day old
    if existing_scrobble_more_than_a_day_old:
        logger.info(
            'Found a scrobble for this video more than a day old, creating a new scrobble'
        )
        scrobble = existing_in_progress_scrobble
        scrobble_created = False
    else:
        if existing_scrobble_more_than_a_day_old and delete_stale_scrobbles:
            existing_in_progress_scrobble.delete()
        scrobble, scrobble_created = Scrobble.objects.get_or_create(
            **scrobble_dict
        )

    if scrobble_created:
        # If we newly created this, capture the client we're watching from
        scrobble.source = data_dict['ClientName']
        scrobble.source_id = data_dict['MediaSourceId']
        scrobble.scrobble_log = ""

    # Update a found scrobble with new position and timestamp
    scrobble.playback_position_ticks = data_dict["PlaybackPositionTicks"]
    scrobble.playback_position = data_dict["PlaybackPosition"]
    scrobble.timestamp = parse(data_dict["UtcTimestamp"])
    scrobble.is_paused = data_dict["IsPaused"] in TRUTHY_VALUES
    scrobble.save(
        update_fields=[
            'playback_position_ticks',
            'playback_position',
            'timestamp',
            'is_paused',
        ]
    )

    # If we hit our completion threshold, save it and get ready
    # to scrobble again if we re-watch this.
    if scrobble.percent_played >= getattr(
        settings, "PERCENT_FOR_COMPLETION", 95
    ):
        scrobble.in_progress = False
        scrobble.playback_position_ticks = video.run_time_ticks
        scrobble.save()

    if scrobble.percent_played % 5 == 0:
        if getattr(settings, "KEEP_DETAILED_SCROBBLE_LOGS", False):
            scrobble.scrobble_log += f"\n{str(scrobble.timestamp)} - {scrobble.playback_position} - {str(scrobble.playback_position_ticks)} - {str(scrobble.percent_played)}%"
            scrobble.save(update_fields=['scrobble_log'])
        logger.debug(f"You are {scrobble.percent_played}% through {video}")

    return Response(video_dict, status=status.HTTP_201_CREATED)
