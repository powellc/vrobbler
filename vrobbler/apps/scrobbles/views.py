import json
import logging

import pytz
from django.conf import settings
from django.db.models.fields import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView
from django.views.generic.list import ListView
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from scrobbles.constants import (
    JELLYFIN_AUDIO_ITEM_TYPES,
    JELLYFIN_VIDEO_ITEM_TYPES,
)
from scrobbles.forms import ScrobbleForm
from scrobbles.imdb import lookup_video_from_imdb
from scrobbles.models import Scrobble
from scrobbles.scrobblers import (
    jellyfin_scrobble_track,
    jellyfin_scrobble_video,
    manual_scrobble_event,
    manual_scrobble_video,
    mopidy_scrobble_podcast,
    mopidy_scrobble_track,
)
from scrobbles.serializers import ScrobbleSerializer
from scrobbles.thesportsdb import lookup_event_from_thesportsdb

from vrobbler.apps.music.aggregators import (
    scrobble_counts,
    top_artists,
    top_tracks,
    week_of_scrobbles,
)

logger = logging.getLogger(__name__)


class RecentScrobbleList(ListView):
    model = Scrobble

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        if user.is_authenticated:
            if user.profile:
                timezone.activate(pytz.timezone(user.profile.timezone))
                now = timezone.localtime(timezone.now())
            data['now_playing_list'] = Scrobble.objects.filter(
                in_progress=True,
                is_paused=False,
                timestamp__lte=now,
                user=user,
            )

            completed_for_user = Scrobble.objects.filter(
                played_to_completion=True, user=user
            )
            data['video_scrobble_list'] = completed_for_user.filter(
                video__isnull=False
            ).order_by('-timestamp')[:15]

            data['podcast_scrobble_list'] = completed_for_user.filter(
                podcast_episode__isnull=False
            ).order_by('-timestamp')[:15]

            data['sport_scrobble_list'] = completed_for_user.filter(
                sport_event__isnull=False
            ).order_by('-timestamp')[:15]

            # data['top_daily_tracks'] = top_tracks()
            data['top_weekly_tracks'] = top_tracks(user, filter='week')
            data['top_monthly_tracks'] = top_tracks(user, filter='month')

            # data['top_daily_artists'] = top_artists()
            data['top_weekly_artists'] = top_artists(user, filter='week')
            data['top_monthly_artists'] = top_artists(user, filter='month')

        data["weekly_data"] = week_of_scrobbles(user=user)

        data['counts'] = scrobble_counts(user)
        data['imdb_form'] = ScrobbleForm
        return data

    def get_queryset(self):
        return Scrobble.objects.filter(
            track__isnull=False, in_progress=False
        ).order_by('-timestamp')[:15]


class ManualScrobbleView(FormView):
    form_class = ScrobbleForm
    template_name = 'scrobbles/manual_form.html'

    def form_valid(self, form):

        item_id = form.cleaned_data.get('item_id')
        data_dict = None
        if 'tt' in item_id:
            data_dict = lookup_video_from_imdb(
                form.cleaned_data.get('item_id')
            )
            if data_dict:
                manual_scrobble_video(data_dict, self.request.user.id)

        if not data_dict:
            logger.debug(f"Looking for sport event with ID {item_id}")
            data_dict = lookup_event_from_thesportsdb(
                form.cleaned_data.get('item_id')
            )
            if data_dict:
                manual_scrobble_event(data_dict, self.request.user.id)

        return HttpResponseRedirect(reverse("home"))


@csrf_exempt
@api_view(['GET'])
def scrobble_endpoint(request):
    """List all Scrobbles, or create a new Scrobble"""
    scrobble = Scrobble.objects.all()
    serializer = ScrobbleSerializer(scrobble, many=True)
    return Response(serializer.data)


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def jellyfin_websocket(request):
    data_dict = request.data

    # For making things easier to build new input processors
    if getattr(settings, "DUMP_REQUEST_DATA", False):
        json_data = json.dumps(data_dict, indent=4)
        logger.debug(f"{json_data}")

    scrobble = None
    media_type = data_dict.get("ItemType", "")

    if media_type in JELLYFIN_AUDIO_ITEM_TYPES:
        scrobble = jellyfin_scrobble_track(data_dict, request.user.id)

    if media_type in JELLYFIN_VIDEO_ITEM_TYPES:
        scrobble = jellyfin_scrobble_video(data_dict, request.user.id)

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'scrobble_id': scrobble.id}, status=status.HTTP_200_OK)


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def mopidy_websocket(request):
    try:
        data_dict = json.loads(request.data)
    except TypeError:
        logger.warning('Received Mopidy data as dict, rather than a string')
        data_dict = request.data

    # For making things easier to build new input processors
    if getattr(settings, "DUMP_REQUEST_DATA", False):
        json_data = json.dumps(data_dict, indent=4)
        logger.debug(f"{json_data}")

    if 'podcast' in data_dict.get('mopidy_uri'):
        scrobble = mopidy_scrobble_podcast(data_dict, request.user.id)
    else:
        scrobble = mopidy_scrobble_track(data_dict, request.user.id)

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'scrobble_id': scrobble.id}, status=status.HTTP_200_OK)


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def scrobble_finish(request, uuid):
    user = request.user
    if not user.is_authenticated:
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    scrobble = Scrobble.objects.filter(user=user, uuid=uuid).first()
    if not scrobble:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    scrobble.stop(force_finish=True)
    return Response(
        {'id': scrobble.id, 'status': scrobble.status},
        status=status.HTTP_200_OK,
    )


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def scrobble_cancel(request, uuid):
    user = request.user
    if not user.is_authenticated:
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    scrobble = Scrobble.objects.filter(user=user, uuid=uuid).first()
    if not scrobble:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    scrobble.cancel()
    return Response(
        {'id': scrobble.id, 'status': 'cancelled'}, status=status.HTTP_200_OK
    )
