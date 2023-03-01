import calendar
import json
import logging
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.fields import timezone
from django.db.models.query import QuerySet
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, FormView, TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from music.aggregators import scrobble_counts, week_of_scrobbles
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from scrobbles.api import serializers
from scrobbles.constants import (
    JELLYFIN_AUDIO_ITEM_TYPES,
    JELLYFIN_VIDEO_ITEM_TYPES,
)
from scrobbles.export import export_scrobbles
from scrobbles.forms import ExportScrobbleForm, ScrobbleForm
from scrobbles.imdb import lookup_video_from_imdb
from scrobbles.models import (
    AudioScrobblerTSVImport,
    ChartRecord,
    KoReaderImport,
    LastFmImport,
    Scrobble,
)
from scrobbles.scrobblers import (
    jellyfin_scrobble_track,
    jellyfin_scrobble_video,
    manual_scrobble_event,
    manual_scrobble_video,
    mopidy_scrobble_podcast,
    mopidy_scrobble_track,
)
from scrobbles.tasks import (
    process_koreader_import,
    process_lastfm_import,
    process_tsv_import,
)
from scrobbles.thesportsdb import lookup_event_from_thesportsdb

from vrobbler.apps.music.aggregators import live_charts

logger = logging.getLogger(__name__)


class RecentScrobbleList(ListView):
    model = Scrobble

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:

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
            data['active_imports'] = AudioScrobblerTSVImport.objects.filter(
                processing_started__isnull=False,
                processed_finished__isnull=True,
                user=self.request.user,
            )

        data["weekly_data"] = week_of_scrobbles(user=user)

        data['counts'] = scrobble_counts(user)
        data['imdb_form'] = ScrobbleForm
        data['export_form'] = ExportScrobbleForm
        return data

    def get_queryset(self):
        return Scrobble.objects.filter(
            track__isnull=False, in_progress=False
        ).order_by('-timestamp')[:15]


class ScrobbleImportListView(TemplateView):
    template_name = "scrobbles/import_list.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['object_list'] = []

        context_data["tsv_imports"] = AudioScrobblerTSVImport.objects.filter(
            user=self.request.user,
        ).order_by('-processing_started')
        context_data["koreader_imports"] = KoReaderImport.objects.filter(
            user=self.request.user,
        ).order_by('-processing_started')
        context_data["lastfm_imports"] = LastFmImport.objects.filter(
            user=self.request.user,
        ).order_by('-processing_started')
        return context_data


class BaseScrobbleImportDetailView(DetailView):
    slug_field = 'uuid'
    template_name = "scrobbles/import_detail.html"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        title = "Generic Scrobble Import"
        if self.model == KoReaderImport:
            title = "KoReader Import"
        if self.model == AudioScrobblerTSVImport:
            title = "Audioscrobbler TSV Import"
        if self.model == LastFmImport:
            title = "LastFM Import"
        context_data['title'] = title
        return context_data


class ScrobbleKoReaderImportDetailView(BaseScrobbleImportDetailView):
    model = KoReaderImport


class ScrobbleTSVImportDetailView(BaseScrobbleImportDetailView):
    model = AudioScrobblerTSVImport


class ScrobbleLastFMImportDetailView(BaseScrobbleImportDetailView):
    model = LastFmImport


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

        return HttpResponseRedirect(reverse("vrobbler-home"))


class JsonableResponseMixin:
    """
    Mixin to add JSON support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.accepts('text/html'):
            return response
        else:
            return JsonResponse(form.errors, status=400)

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if self.request.accepts('text/html'):
            return response
        else:
            data = {
                'pk': self.object.pk,
            }
            return JsonResponse(data)


class AudioScrobblerImportCreateView(
    LoginRequiredMixin, JsonableResponseMixin, CreateView
):
    model = AudioScrobblerTSVImport
    fields = ['tsv_file']
    template_name = 'scrobbles/upload_form.html'
    success_url = reverse_lazy('vrobbler-home')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        process_tsv_import.delay(self.object.id)
        return HttpResponseRedirect(self.get_success_url())


class KoReaderImportCreateView(
    LoginRequiredMixin, JsonableResponseMixin, CreateView
):
    model = KoReaderImport
    fields = ['sqlite_file']
    template_name = 'scrobbles/upload_form.html'
    success_url = reverse_lazy('vrobbler-home')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        process_koreader_import.delay(self.object.id)
        return HttpResponseRedirect(self.get_success_url())


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def lastfm_import(request):
    lfm_import, created = LastFmImport.objects.get_or_create(
        user=request.user, processed_finished__isnull=True
    )

    process_lastfm_import.delay(lfm_import.id)

    success_url = reverse_lazy('vrobbler-home')
    return HttpResponseRedirect(success_url)


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def jellyfin_webhook(request):
    data_dict = request.data

    if (
        data_dict['NotificationType'] == 'PlaybackProgress'
        and data_dict['ItemType'] == 'Audio'
    ):
        return Response({}, status=status.HTTP_304_NOT_MODIFIED)

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
def mopidy_webhook(request):
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
@api_view(['POST'])
@parser_classes([MultiPartParser])
def import_audioscrobbler_file(request):
    """Takes a TSV file in the Audioscrobbler format, saves it and processes the
    scrobbles.
    """
    scrobbles_created = []
    # tsv_file = request.FILES[0]

    file_serializer = serializers.AudioScrobblerTSVImportSerializer(
        data=request.data
    )
    if file_serializer.is_valid():
        import_file = file_serializer.save()
        return Response(
            {'scrobble_ids': scrobbles_created}, status=status.HTTP_200_OK
        )
    else:
        return Response(
            file_serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def scrobble_finish(request, uuid):
    user = request.user
    success_url = reverse_lazy('vrobbler-home')

    if not user.is_authenticated:
        return HttpResponseRedirect(success_url)

    scrobble = Scrobble.objects.filter(user=user, uuid=uuid).first()
    if scrobble:
        scrobble.stop(force_finish=True)
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Scrobble of {scrobble.media_obj} finished.",
        )
    else:
        messages.add_message(request, messages.ERROR, "Scrobble not found.")
    return HttpResponseRedirect(success_url)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def scrobble_cancel(request, uuid):
    user = request.user
    success_url = reverse_lazy('vrobbler-home')

    if not user.is_authenticated:
        return HttpResponseRedirect(success_url)

    scrobble = Scrobble.objects.filter(user=user, uuid=uuid).first()
    if scrobble:
        scrobble.cancel()
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Scrobble of {scrobble.media_obj} cancelled.",
        )
    else:
        messages.add_message(request, messages.ERROR, "Scrobble not found.")
    return HttpResponseRedirect(success_url)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def export(request):
    format = request.GET.get('export_type', 'csv')
    start = request.GET.get('start')
    end = request.GET.get('end')
    logger.debug(f"Exporting all scrobbles in format {format}")

    temp_file, extension = export_scrobbles(
        start_date=start, end_date=end, format=format
    )

    now = datetime.now()
    filename = f"vrobbler-export-{str(now)}.{extension}"
    response = FileResponse(open(temp_file, 'rb'))
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


class ChartRecordView(TemplateView):
    template_name = 'scrobbles/chart_index.html'

    @staticmethod
    def get_media_filter(media_type: str = "") -> Q:
        filters = {
            "Track": Q(track__isnull=False),
            "Artist": Q(artist__isnull=False),
            "Series": Q(series__isnull=False),
            "Video": Q(video__isnull=False),
            "": Q(),
        }
        return filters[media_type]

    def get_chart_records(self, media_type: str = "", **kwargs):
        media_filter = self.get_media_filter(media_type)
        charts = ChartRecord.objects.filter(
            media_filter, user=self.request.user, **kwargs
        ).order_by("rank")

        if charts.count() == 0:
            ChartRecord.build(
                user=self.request.user, model_str=media_type, **kwargs
            )
            charts = ChartRecord.objects.filter(
                media_filter, user=self.request.user, **kwargs
            ).order_by("rank")
        return charts

    def get_chart(
        self, period: str = "all_time", limit=15, media: str = ""
    ) -> QuerySet:
        now = timezone.now()
        params = {}
        params['media_type'] = media
        if period == "today":
            params['day'] = now.day
            params['month'] = now.month
            params['year'] = now.year
        if period == "week":
            params['week'] = now.ioscalendar()[1]
            params['year'] = now.year
        if period == "month":
            params['month'] = now.month
            params['year'] = now.year
        if period == "year":
            params['year'] = now.year
        return self.get_chart_records(**params)[:limit]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        date = self.request.GET.get("date")
        media_type = self.request.GET.get("media", "Track")
        user = self.request.user
        params = {}
        context_data["artist_charts"] = {}

        if not date:
            artist_params = {'user': user, 'media_type': 'Artist'}
            context_data['current_artist_charts'] = {
                "today": live_charts(**artist_params, chart_period="today"),
                "week": live_charts(**artist_params, chart_period="week"),
                "month": live_charts(**artist_params, chart_period="month"),
                "all": live_charts(**artist_params),
            }

            track_params = {'user': user, 'media_type': 'Track'}
            context_data['current_track_charts'] = {
                "today": live_charts(**track_params, chart_period="today"),
                "week": live_charts(**track_params, chart_period="week"),
                "month": live_charts(**track_params, chart_period="month"),
                "all": live_charts(**track_params),
            }
            return context_data

        # Date provided, lookup past charts, returning nothing if it's now or in the future.
        now = timezone.now()
        year = now.year
        params = {'year': year}
        name = f"Chart for {year}"

        date_params = date.split('-')
        year = int(date_params[0])
        in_progress = False
        if len(date_params) == 2:
            if 'W' in date_params[1]:
                week = int(date_params[1].strip('W"'))
                params['week'] = week
                start = datetime.strptime(date + "-1", "%Y-W%W-%w").replace(
                    tzinfo=pytz.utc
                )
                end = start + timedelta(days=6)
                in_progress = start <= now <= end
                as_str = start.strftime('Week of %B %d, %Y')
                name = f"Chart for {as_str}"
            else:
                month = int(date_params[1])
                params['month'] = month
                month_str = calendar.month_name[month]
                name = f"Chart for {month_str} {year}"
                in_progress = now.month == month and now.year == year
        if len(date_params) == 3:
            month = int(date_params[1])
            day = int(date_params[2])
            params['month'] = month
            params['day'] = day
            month_str = calendar.month_name[month]
            name = f"Chart for {month_str} {day}, {year}"
            in_progress = (
                now.month == month and now.year == year and now.day == day
            )

        media_filter = self.get_media_filter("Track")
        track_charts = ChartRecord.objects.filter(
            media_filter, user=self.request.user, **params
        ).order_by("rank")
        media_filter = self.get_media_filter("Artist")
        artist_charts = ChartRecord.objects.filter(
            media_filter, user=self.request.user, **params
        ).order_by("rank")

        if track_charts.count() == 0 and not in_progress:
            ChartRecord.build(
                user=self.request.user, model_str="Track", **params
            )
            media_filter = self.get_media_filter("Track")
            track_charts = ChartRecord.objects.filter(
                media_filter, user=self.request.user, **params
            ).order_by("rank")
        if artist_charts.count() == 0 and not in_progress:
            ChartRecord.build(
                user=self.request.user, model_str="Artist", **params
            )
            media_filter = self.get_media_filter("Artist")
            artist_charts = ChartRecord.objects.filter(
                media_filter, user=self.request.user, **params
            ).order_by("rank")

        context_data['media_type'] = media_type
        context_data['track_charts'] = track_charts
        context_data['artist_charts'] = artist_charts
        context_data['name'] = " ".join(["Top", media_type, "for", name])
        context_data['in_progress'] = in_progress
        return context_data
