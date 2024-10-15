import calendar
import json
import logging
from datetime import datetime, timedelta

import pytz
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, FormView, TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from music.aggregators import live_charts, scrobble_counts, week_of_scrobbles
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
    LONG_PLAY_MEDIA,
    MANUAL_SCROBBLE_FNS,
    PLAY_AGAIN_MEDIA,
    SCROBBLE_CONTENT_URLS,
)
from scrobbles.export import export_scrobbles
from scrobbles.forms import ExportScrobbleForm, ScrobbleForm
from scrobbles.models import (
    AudioScrobblerTSVImport,
    ChartRecord,
    KoReaderImport,
    LastFmImport,
    RetroarchImport,
    Scrobble,
)
from scrobbles.scrobblers import *
from scrobbles.tasks import (
    process_koreader_import,
    process_lastfm_import,
    process_tsv_import,
)
from scrobbles.utils import (
    get_long_plays_completed,
    get_long_plays_in_progress,
    get_recently_played_board_games,
)

logger = logging.getLogger(__name__)


class ScrobbleableListView(ListView):
    model = None
    paginate_by = 200

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_anonymous:
            queryset = queryset.annotate(
                scrobble_count=Count("scrobble"),
                filter=Q(scrobble__user=self.request.user),
            ).order_by("-scrobble_count")
        else:
            queryset = queryset.annotate(
                scrobble_count=Count("scrobble")
            ).order_by("-scrobble_count")
        return queryset


class ScrobbleableDetailView(DetailView):
    model = None
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["scrobbles"] = list()
        if not self.request.user.is_anonymous:
            context_data["scrobbles"] = self.object.scrobble_set.filter(
                user=self.request.user
            )
        return context_data


class RecentScrobbleList(ListView):
    model = Scrobble

    def get(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            if scrobble_url := self.request.GET.get("scrobble_url", ""):
                scrobble = manual_scrobble_from_url(
                    scrobble_url, self.request.user.id
                )
                return HttpResponseRedirect(scrobble.redirect_url(user.id))
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:

            completed_for_user = Scrobble.objects.filter(
                played_to_completion=True, user=user
            )
            data["long_play_in_progress"] = get_long_plays_in_progress(user)
            data["play_again"] = get_recently_played_board_games(user)
            data["video_scrobble_list"] = completed_for_user.filter(
                video__isnull=False
            ).order_by("-timestamp")[:15]

            data["podcast_scrobble_list"] = completed_for_user.filter(
                podcast_episode__isnull=False
            ).order_by("-timestamp")[:15]

            data["sport_scrobble_list"] = completed_for_user.filter(
                sport_event__isnull=False
            ).order_by("-timestamp")[:15]

            data["videogame_scrobble_list"] = completed_for_user.filter(
                video_game__isnull=False
            ).order_by("-timestamp")[:15]

            data["boardgame_scrobble_list"] = completed_for_user.filter(
                board_game__isnull=False
            ).order_by("-timestamp")[:15]

            data["active_imports"] = AudioScrobblerTSVImport.objects.filter(
                processing_started__isnull=False,
                processed_finished__isnull=True,
                user=self.request.user,
            )
            data["counts"] = scrobble_counts(user)
        else:
            data["weekly_data"] = week_of_scrobbles()
            data["counts"] = scrobble_counts()

        data["imdb_form"] = ScrobbleForm
        data["export_form"] = ExportScrobbleForm
        return data

    def get_queryset(self):
        return Scrobble.objects.filter(
            track__isnull=False, in_progress=False
        ).order_by("-timestamp")[:15]


class ScrobbleLongPlaysView(TemplateView):
    template_name = "scrobbles/long_plays_in_progress.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["view"] = self.request.GET.get("view", "grid")
        context_data["in_progress"] = get_long_plays_in_progress(
            self.request.user
        )
        context_data["completed"] = get_long_plays_completed(self.request.user)
        return context_data


class ScrobbleImportListView(TemplateView):
    template_name = "scrobbles/import_list.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["object_list"] = []

        context_data["tsv_imports"] = AudioScrobblerTSVImport.objects.filter(
            user=self.request.user,
        ).order_by("-processing_started")[:10]
        context_data["koreader_imports"] = KoReaderImport.objects.filter(
            user=self.request.user,
        ).order_by("-processing_started")[:10]
        context_data["lastfm_imports"] = LastFmImport.objects.filter(
            user=self.request.user,
        ).order_by("-processing_started")[:10]
        context_data["retroarch_imports"] = RetroarchImport.objects.filter(
            user=self.request.user,
        ).order_by("-processing_started")[:10]
        return context_data


class BaseScrobbleImportDetailView(DetailView):
    slug_field = "uuid"
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
        if self.model == RetroarchImport:
            title = "Retroarch Import"
        context_data["title"] = title
        return context_data


class ScrobbleKoReaderImportDetailView(BaseScrobbleImportDetailView):
    model = KoReaderImport


class ScrobbleTSVImportDetailView(BaseScrobbleImportDetailView):
    model = AudioScrobblerTSVImport


class ScrobbleLastFMImportDetailView(BaseScrobbleImportDetailView):
    model = LastFmImport


class ScrobbleRetroarchImportDetailView(BaseScrobbleImportDetailView):
    model = RetroarchImport


class ManualScrobbleView(FormView):
    form_class = ScrobbleForm
    template_name = "scrobbles/manual_form.html"

    def form_valid(self, form):
        item_str = form.cleaned_data.get("item_id")
        logger.debug(f"Looking for scrobblable media with input {item_str}")

        key, item_id = item_str[:2], item_str[3:]
        scrobble_fn = MANUAL_SCROBBLE_FNS[key]
        scrobble = eval(scrobble_fn)(item_id, self.request.user.id)

        return HttpResponseRedirect(
            scrobble.redirect_url(self.request.user.id)
        )


class JsonableResponseMixin:
    """
    Mixin to add JSON support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.accepts("text/html"):
            return response
        else:
            return JsonResponse(form.errors, status=400)

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if self.request.accepts("text/html"):
            return response
        else:
            data = {
                "pk": self.object.pk,
            }
            return JsonResponse(data)


class AudioScrobblerImportCreateView(
    LoginRequiredMixin, JsonableResponseMixin, CreateView
):
    model = AudioScrobblerTSVImport
    fields = ["tsv_file"]
    template_name = "scrobbles/upload_form.html"
    success_url = reverse_lazy("vrobbler-home")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        process_tsv_import.delay(self.object.id)
        return HttpResponseRedirect(self.request.META.get("HTTP_REFERER"))


class KoReaderImportCreateView(
    LoginRequiredMixin, JsonableResponseMixin, CreateView
):
    model = KoReaderImport
    fields = ["sqlite_file"]
    template_name = "scrobbles/upload_form.html"
    success_url = reverse_lazy("vrobbler-home")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        process_koreader_import.delay(self.object.id)
        return HttpResponseRedirect(self.request.META.get("HTTP_REFERER"))


@permission_classes([IsAuthenticated])
@api_view(["GET"])
def lastfm_import(request):
    lfm_import, created = LastFmImport.objects.get_or_create(
        user=request.user, processed_finished__isnull=True
    )

    process_lastfm_import.delay(lfm_import.id)

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(["POST"])
def jellyfin_webhook(request):
    post_data = request.data
    logger.info(
        "[jellyfin_webhook] called",
        extra={"post_data": post_data},
    )

    in_progress = post_data.get("NotificationType", "") == "PlaybackProgress"
    is_music = post_data.get("ItemType", "") == "Audio"

    # Disregard progress updates
    if in_progress and is_music:
        logger.info(
            "[jellyfin_webhook] ignoring update of music in progress",
            extra={"post_data": post_data},
        )
        return Response({}, status=status.HTTP_304_NOT_MODIFIED)

    scrobble = jellyfin_scrobble_media(post_data, request.user.id)

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(
        "[jellyfin_webhook] finished",
        extra={"scrobble_id": scrobble.id},
    )
    return Response({"scrobble_id": scrobble.id}, status=status.HTTP_200_OK)


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(["POST"])
def mopidy_webhook(request):
    try:
        data_dict = json.loads(request.data)
    except TypeError:
        data_dict = request.data

    scrobble = mopidy_scrobble_media(data_dict, request.user.id)

    if not scrobble:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"scrobble_id": scrobble.id}, status=status.HTTP_200_OK)


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(["POST"])
def gps_webhook(request):
    try:
        data_dict = json.loads(request.data)
    except TypeError:
        data_dict = request.data

    # For making things easier to build new input processors
    if getattr(settings, "DUMP_REQUEST_DATA", False):
        json_data = json.dumps(data_dict, indent=4)
        logger.debug(f"{json_data}")

    # TODO Fix this so we have to authenticate!
    user_id = 1
    if request.user.id:
        user_id = request.user.id

    scrobble = gpslogger_scrobble_location(data_dict, user_id)

    if not scrobble:
        return Response({}, status=status.HTTP_200_OK)

    return Response({"scrobble_id": scrobble.id}, status=status.HTTP_200_OK)


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(["POST"])
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
            {"scrobble_ids": scrobbles_created}, status=status.HTTP_200_OK
        )
    else:
        return Response(
            file_serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


@permission_classes([IsAuthenticated])
@api_view(["GET"])
def scrobble_start(request, uuid):
    logger.info(
        "[scrobble_start] called",
        extra={"request": request, "uuid": uuid},
    )
    user = request.user
    success_url = request.META.get("HTTP_REFERER")

    if not user.is_authenticated:
        return HttpResponseRedirect(success_url)

    media_obj = None
    for app, model in PLAY_AGAIN_MEDIA.items():
        media_model = apps.get_model(app_label=app, model_name=model)
        media_obj = media_model.objects.filter(uuid=uuid).first()
        if media_obj:
            break

    if not media_obj:
        logger.info(
            "[scrobble_start] media object not found",
            extra={"uuid": uuid, "user_id": user.id},
        )
        # TODO Log that we couldn't find a media obj to scrobble
        return

    scrobble = None
    user_id = request.user.id
    if media_obj:
        media_obj.scrobble_for_user(user_id)

    if scrobble:
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Scrobble of {scrobble.media_obj} started.",
        )
    else:
        messages.add_message(
            request, messages.ERROR, f"Media with uuid {uuid} not found."
        )

    if (
        user.profile.redirect_to_webpage
        and media_obj.__class__.__name__ == Scrobble.MediaType.WEBPAGE
    ):
        logger.info(f"Redirecting to {media_obj} detail apge")
        return HttpResponseRedirect(media_obj.url)

    return HttpResponseRedirect(success_url)


@api_view(["GET"])
def scrobble_longplay_finish(request, uuid):
    user = request.user
    success_url = request.META.get("HTTP_REFERER")

    if not user.is_authenticated:
        return HttpResponseRedirect(success_url)

    media_obj = None
    for app, model in LONG_PLAY_MEDIA.items():
        media_model = apps.get_model(app_label=app, model_name=model)
        media_obj = media_model.objects.filter(uuid=uuid).first()
        if media_obj:
            break

    if not media_obj:
        return

    last_scrobble = media_obj.last_long_play_scrobble_for_user(user)
    if last_scrobble and last_scrobble.long_play_complete == False:
        last_scrobble.long_play_complete = True
        last_scrobble.save(update_fields=["long_play_complete"])
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Long play of {media_obj} finished.",
        )
    else:
        messages.add_message(
            request, messages.ERROR, f"Media with uuid {uuid} not found."
        )
    return HttpResponseRedirect(success_url)


@permission_classes([IsAuthenticated])
@api_view(["GET"])
def scrobble_finish(request, uuid):
    user = request.user
    success_url = request.META.get("HTTP_REFERER")

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
@api_view(["GET"])
def scrobble_cancel(request, uuid):
    user = request.user
    success_url = reverse_lazy("vrobbler-home")

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
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@permission_classes([IsAuthenticated])
@api_view(["GET"])
def export(request):
    format = request.GET.get("export_type", "csv")
    start = request.GET.get("start")
    end = request.GET.get("end")
    logger.debug(f"Exporting all scrobbles in format {format}")

    temp_file, extension = export_scrobbles(
        start_date=start, end_date=end, format=format
    )

    now = datetime.now()
    filename = f"vrobbler-export-{str(now)}.{extension}"
    response = FileResponse(open(temp_file, "rb"))
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


class ChartRecordView(TemplateView):
    template_name = "scrobbles/chart_index.html"

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
        params["media_type"] = media
        if period == "today":
            params["day"] = now.day
            params["month"] = now.month
            params["year"] = now.year
        if period == "week":
            params["week"] = now.ioscalendar()[1]
            params["year"] = now.year
        if period == "month":
            params["month"] = now.month
            params["year"] = now.year
        if period == "year":
            params["year"] = now.year
        return self.get_chart_records(**params)[:limit]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        date = self.request.GET.get("date")
        media_type = self.request.GET.get("media", "Track")
        user = self.request.user
        params = {}
        context_data["artist_charts"] = {}

        if not date:
            limit = 20
            artist_params = {"user": user, "media_type": "Artist"}
            context_data["current_artist_charts"] = {
                "today": live_charts(
                    **artist_params, chart_period="today", limit=limit
                ),
                "week": live_charts(
                    **artist_params, chart_period="week", limit=limit
                ),
                "month": live_charts(
                    **artist_params, chart_period="month", limit=limit
                ),
                "year": live_charts(
                    **artist_params, chart_period="year", limit=limit
                ),
                "all": live_charts(**artist_params, limit=limit),
            }

            track_params = {"user": user, "media_type": "Track"}
            context_data["current_track_charts"] = {
                "today": live_charts(
                    **track_params, chart_period="today", limit=limit
                ),
                "week": live_charts(
                    **track_params, chart_period="week", limit=limit
                ),
                "month": live_charts(
                    **track_params, chart_period="month", limit=limit
                ),
                "year": live_charts(
                    **track_params, chart_period="year", limit=limit
                ),
                "all": live_charts(**track_params, limit=limit),
            }

            limit = 14
            artist = {"user": user, "media_type": "Artist", "limit": limit}
            # This is weird. They don't display properly as QuerySets, so we cast to lists
            context_data["chart_keys"] = {
                "today": "Today",
                "last7": "Last 7 days",
                "last30": "Last 30 days",
                "year": "This year",
                "all": "All time",
            }
            context_data["current_artist_charts"] = {
                "today": list(live_charts(**artist, chart_period="today")),
                "last7": list(live_charts(**artist, chart_period="last7")),
                "last30": list(live_charts(**artist, chart_period="last30")),
                "year": list(live_charts(**artist, chart_period="year")),
                "all": list(live_charts(**artist)),
            }

            track = {"user": user, "media_type": "Track", "limit": limit}
            context_data["current_track_charts"] = {
                "today": list(live_charts(**track, chart_period="today")),
                "last7": list(live_charts(**track, chart_period="last7")),
                "last30": list(live_charts(**track, chart_period="last30")),
                "year": list(live_charts(**track, chart_period="year")),
                "all": list(live_charts(**track)),
            }
            return context_data

        # Date provided, lookup past charts, returning nothing if it's now or in the future.
        now = timezone.now()
        year = now.year
        params = {"year": year}
        name = f"Chart for {year}"

        date_params = date.split("-")
        year = int(date_params[0])
        in_progress = False
        if len(date_params) == 2:
            if "W" in date_params[1]:
                week = int(date_params[1].strip('W"'))
                params["week"] = week
                start = datetime.strptime(date + "-1", "%Y-W%W-%w").replace(
                    tzinfo=pytz.utc
                )
                end = start + timedelta(days=6)
                in_progress = start <= now <= end
                as_str = start.strftime("Week of %B %d, %Y")
                name = f"Chart for {as_str}"
            else:
                month = int(date_params[1])
                params["month"] = month
                month_str = calendar.month_name[month]
                name = f"Chart for {month_str} {year}"
                in_progress = now.month == month and now.year == year
        if len(date_params) == 3:
            month = int(date_params[1])
            day = int(date_params[2])
            params["month"] = month
            params["day"] = day
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

        context_data["media_type"] = media_type
        context_data["track_charts"] = track_charts
        context_data["artist_charts"] = artist_charts
        context_data["name"] = " ".join(["Top", media_type, "for", name])
        context_data["in_progress"] = in_progress
        return context_data


class ScrobbleStatusView(LoginRequiredMixin, TemplateView):
    model = Scrobble
    template_name = "scrobbles/status.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        user_scrobble_qs = Scrobble.objects.filter().order_by("-timestamp")
        progress_plays = user_scrobble_qs.filter(
            in_progress=True, is_paused=False
        )

        data["listening"] = progress_plays.filter(
            Q(track__isnull=False) | Q(podcast_episode__isnull=False)
        ).first()
        data["watching"] = progress_plays.filter(video__isnull=False).first()
        data["going"] = progress_plays.filter(
            geo_location__isnull=False
        ).first()
        data["playing"] = progress_plays.filter(
            board_game__isnull=False
        ).first()
        data["sporting"] = progress_plays.filter(
            sport_event__isnull=False
        ).first()
        data["browsing"] = progress_plays.filter(
            web_page__isnull=False
        ).first()
        data["participating"] = progress_plays.filter(
            life_event__isnull=False
        ).first()
        data["working"] = progress_plays.filter(task__isnull=False).first()

        long_plays = user_scrobble_qs.filter(
            long_play_complete=False, played_to_completion=True
        )
        data["reading"] = long_plays.filter(book__isnull=False).first()
        data["sessioning"] = long_plays.filter(
            video_game__isnull=False
        ).first()

        return data
