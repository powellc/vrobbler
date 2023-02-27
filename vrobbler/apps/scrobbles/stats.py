import calendar
import logging
from datetime import datetime, timedelta
from typing import Optional

import pytz
from django.apps import apps
from django.conf import settings
from django.db.models import Count, Q, ExpressionWrapper, OuterRef, Subquery


logger = logging.getLogger(__name__)


def get_start_end_dates_by_week(year, week, tz):
    d = datetime(year, 1, 1, tzinfo=tz)
    if d.weekday() <= 3:
        d = d - timedelta(d.weekday())
    else:
        d = d + timedelta(7 - d.weekday())
    dlt = timedelta(days=(week - 1) * 7)
    return d + dlt, d + dlt + timedelta(days=6)


def get_scrobble_count_qs(
    year: Optional[int] = None,
    month: Optional[int] = None,
    week: Optional[int] = None,
    day: Optional[int] = None,
    user=None,
    model_str="Track",
) -> dict[str, int]:
    tz = settings.TIME_ZONE
    if user and user.is_authenticated:
        tz = pytz.timezone(user.profile.timezone)

    tz = pytz.utc
    data_model = apps.get_model(app_label='music', model_name='Track')
    if model_str == "Artist":
        data_model = apps.get_model(app_label='music', model_name='Artist')
    if model_str == "Video":
        data_model = apps.get_model(app_label='videos', model_name='Video')
    if model_str == "SportEvent":
        data_model = apps.get_model(
            app_label='sports', model_name='SportEvent'
        )

    if model_str == "Artist":
        base_qs = data_model.objects.filter(
            track__scrobble__user=user,
            track__scrobble__played_to_completion=True,
        )
    else:
        base_qs = data_model.objects.filter(
            scrobble__user=user,
            scrobble__played_to_completion=True,
        )

    # Returna all media items with scrobble count annotated
    if not year:
        return base_qs.annotate(scrobble_count=Count("scrobble")).order_by(
            "-scrobble_count"
        )

    start = datetime(year, 1, 1, tzinfo=tz)
    end = datetime(year, 12, 31, tzinfo=tz)

    if year and day and month:
        logger.debug('Filtering by year, month and day')
        start = datetime(year, month, day, 0, 0, tzinfo=tz)
        end = datetime(year, month, day, 23, 59, tzinfo=tz)
    elif year and week:
        logger.debug('Filtering by year and week')
        start, end = get_start_end_dates_by_week(year, week, tz)
    elif month:
        logger.debug('Filtering by month')
        end_day = calendar.monthrange(year, month)[1]
        start = datetime(year, month, 1, tzinfo=tz)
        end = datetime(year, month, end_day, tzinfo=tz)

    if model_str == "Artist":
        scrobble_date_filter = Q(
            track__scrobble__timestamp__gte=start,
            track__scrobble__timestamp__lte=end,
        )
        qs = (
            base_qs.filter(scrobble_date_filter)
            .annotate(scrobble_count=Count("track__scrobble", distinct=True))
            .order_by("-scrobble_count")
        )
    else:
        scrobble_date_filter = Q(
            scrobble__timestamp__gte=start, scrobble__timestamp__lte=end
        )
        qs = (
            base_qs.filter(scrobble_date_filter)
            .annotate(scrobble_count=Count("scrobble", distinct=True))
            .order_by("-scrobble_count")
        )

    return qs


def build_charts(
    year: Optional[int] = None,
    month: Optional[int] = None,
    week: Optional[int] = None,
    day: Optional[int] = None,
    user=None,
    model_str="Track",
):
    ChartRecord = apps.get_model(
        app_label='scrobbles', model_name='ChartRecord'
    )
    results = get_scrobble_count_qs(year, month, week, day, user, model_str)
    unique_counts = list(set([result.scrobble_count for result in results]))
    unique_counts.sort(reverse=True)
    ranks = {}
    for rank, count in enumerate(unique_counts, start=1):
        ranks[count] = rank

    chart_records = []
    for result in results:
        chart_record = {
            'year': year,
            'week': week,
            'month': month,
            'day': day,
            'user': user,
        }
        chart_record['rank'] = ranks[result.scrobble_count]
        chart_record['count'] = result.scrobble_count
        if model_str == 'Track':
            chart_record['track'] = result
        if model_str == 'Video':
            chart_record['video'] = result
        if model_str == 'Artist':
            chart_record['artist'] = result
        chart_records.append(ChartRecord(**chart_record))
    ChartRecord.objects.bulk_create(
        chart_records, ignore_conflicts=True, batch_size=500
    )
