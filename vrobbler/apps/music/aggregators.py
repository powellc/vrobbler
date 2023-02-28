from datetime import datetime, timedelta
from typing import List

from django.apps import apps
from django.db.models import Count, Q, QuerySet
from django.utils import timezone
from music.models import Artist, Track
from scrobbles.models import Scrobble
from videos.models import Video
from vrobbler.apps.profiles.utils import now_user_timezone


def scrobble_counts(user=None):

    now = timezone.now()
    user_filter = Q()
    if user and user.is_authenticated:
        now = now_user_timezone(user.profile)
        user_filter = Q(user=user)

    start_of_today = datetime.combine(
        now.date(), datetime.min.time(), now.tzinfo
    )
    starting_day_of_current_week = now.date() - timedelta(
        days=now.today().isoweekday() % 7
    )
    starting_day_of_current_month = now.date().replace(day=1)
    starting_day_of_current_year = now.date().replace(month=1, day=1)

    finished_scrobbles_qs = Scrobble.objects.filter(
        user_filter, played_to_completion=True
    )
    data = {}
    data['today'] = finished_scrobbles_qs.filter(
        timestamp__gte=start_of_today
    ).count()
    data['week'] = finished_scrobbles_qs.filter(
        timestamp__gte=starting_day_of_current_week
    ).count()
    data['month'] = finished_scrobbles_qs.filter(
        timestamp__gte=starting_day_of_current_month
    ).count()
    data['year'] = finished_scrobbles_qs.filter(
        timestamp__gte=starting_day_of_current_year
    ).count()
    data['alltime'] = finished_scrobbles_qs.count()
    return data


def week_of_scrobbles(
    user=None, start=None, media: str = 'tracks'
) -> dict[str, int]:

    now = timezone.now()
    user_filter = Q()
    if user and user.is_authenticated:
        now = now_user_timezone(user.profile)
        user_filter = Q(user=user)

    if not start:
        start = datetime.combine(now.date(), datetime.min.time(), now.tzinfo)

    scrobble_day_dict = {}
    base_qs = Scrobble.objects.filter(user_filter, played_to_completion=True)

    media_filter = Q(track__isnull=False)
    if media == 'movies':
        media_filter = Q(video__video_type=Video.VideoType.MOVIE)
    if media == 'series':
        media_filter = Q(video__video_type=Video.VideoType.TV_EPISODE)

    for day in range(6, -1, -1):
        start_day = start - timedelta(days=day)
        end = datetime.combine(start_day, datetime.max.time(), now.tzinfo)
        day_of_week = start_day.strftime('%A')

        scrobble_day_dict[day_of_week] = base_qs.filter(
            media_filter,
            timestamp__gte=start_day,
            timestamp__lte=end,
            played_to_completion=True,
        ).count()

    return scrobble_day_dict


def live_charts(
    user: "User",
    media_type: str = "Track",
    chart_period: str = "all",
    limit: int = 15,
) -> QuerySet:
    now = timezone.now()
    tzinfo = now.tzinfo
    now = now.date()
    if user.is_authenticated:
        now = now_user_timezone(user.profile)
        tzinfo = now.tzinfo

    start_of_today = datetime.combine(now, datetime.min.time(), tzinfo)
    start_day_of_week = now - timedelta(days=now.today().isoweekday() % 7)
    start_day_of_month = now.replace(day=1)
    start_day_of_year = now.replace(month=1, day=1)

    media_model = apps.get_model(app_label='music', model_name=media_type)

    period_queries = {
        'today': {'scrobble__timestamp__gte': start_of_today},
        'week': {'scrobble__timestamp__gte': start_day_of_week},
        'month': {'scrobble__timestamp__gte': start_day_of_month},
        'year': {'scrobble__timestamp__gte': start_day_of_year},
        'all': {},
    }

    time_filter = Q()
    completion_filter = Q(
        scrobble__user=user, scrobble__played_to_completion=True
    )
    user_filter = Q(scrobble__user=user)
    count_field = "scrobble"

    if media_type == "Artist":
        for period, query_dict in period_queries.items():
            period_queries[period] = {
                "track__" + k: v for k, v in query_dict.items()
            }
        completion_filter = Q(
            track__scrobble__user=user,
            track__scrobble__played_to_completion=True,
        )
        count_field = "track__scrobble"
        user_filter = Q(track__scrobble__user=user)

    time_filter = Q(**period_queries[chart_period])

    return (
        media_model.objects.filter(user_filter, time_filter)
        .annotate(
            num_scrobbles=Count(
                count_field,
                filter=completion_filter,
                distinct=True,
            )
        )
        .order_by("-num_scrobbles")[:limit]
    )


def artist_scrobble_count(artist_id: int, filter: str = "today") -> int:
    return Scrobble.objects.filter(track__artist=artist_id).count()
