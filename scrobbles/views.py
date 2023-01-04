import json
import logging

import dateutil
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from scrobbles.models import Scrobble
from scrobbles.serializers import ScrobbleSerializer
from videos.models import Series, Video

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


@csrf_exempt
@api_view(['GET', 'POST'])
def scrobble_list(request):
    """List all Scrobbles, or create a new Scrobble"""
    if request.method == 'GET':
        scrobble = Scrobble.objects.all()
        serializer = ScrobbleSerializer(scrobble, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data_dict = json.loads(request.data["_content"])
        media_type = data_dict["ItemType"]
        # Check if it's a TV Episode
        video_dict = {
            "title": data_dict["Name"],
            "imdb_id": data_dict["Provider_imdb"],
            "video_type": Video.VideoType.MOVIE,
        }
        if media_type == 'Episode':
            series_name = data_dict["SeriesName"]
            series = Series.objects.get_or_create(name=series_name)

            video_dict['video_type'] = Video.VideoType.TV_EPISODE
            video_dict["tv_series_id"] = series.id
            video_dict["episode_num"] = data_dict["EpisodeNumber"]
            video_dict["season_num"] = data_dict["SeasonNumber"]
            video_dict["tvdb_id"] = data_dict["Provider_tvdb"]
            video_dict["tvrage_id"] = data_dict["Provider_tvrage"]

        video, _created = Video.objects.get_or_create(**video_dict)

        video.year = data_dict["Year"]
        video.overview = data_dict["Overview"]
        video.tagline = data_dict["Tagline"]
        video.run_time_ticks = data_dict["RunTimeTicks"]
        video.run_time = data_dict["RunTime"]
        video.save()

        # Now we run off a scrobble
        scrobble_dict = {
            'video_id': video.id,
            'user_id': request.user.id,
        }
        scrobble, scrobble_created = Scrobble.objects.get_or_create(
            **scrobble_dict
        )

        if scrobble_created:
            scrobble.source = data_dict['ClientName']
            scrobble.source_id = data_dict['MediaSourceId']

        # Update a found scrobble with new position and timestamp
        scrobble.playback_position_ticks = data_dict["PlaybackPositionTicks"]
        scrobble.playback_position = data_dict["PlaybackPosition"]
        scrobble.timestamp = dateutil.parser.parse(data_dict["UtcTimestamp"])
        scrobble.is_paused = data_dict["IsPaused"] in TRUTHY_VALUES
        scrobble.played_to_completion = (
            data_dict["PlayedToCompletion"] in TRUTHY_VALUES
        )
        scrobble.save()

        logger.info(f"You are {scrobble.percent_played}% through {video}")

        return Response(video_dict, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
