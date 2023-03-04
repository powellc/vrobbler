import calendar
import logging
from datetime import datetime, timedelta
from typing import Optional

import pytz
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

User = get_user_model()

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
    data_model = apps.get_model(app_label="music", model_name="Track")
    if model_str == "Artist":
        data_model = apps.get_model(app_label="music", model_name="Artist")
    if model_str == "Video":
        data_model = apps.get_model(app_label="videos", model_name="Video")
    if model_str == "SportEvent":
        data_model = apps.get_model(
            app_label="sports", model_name="SportEvent"
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
        logger.debug("Filtering by year, month and day")
        start = datetime(year, month, day, 0, 0, tzinfo=tz)
        end = datetime(year, month, day, 23, 59, tzinfo=tz)
    elif year and week:
        logger.debug("Filtering by year and week")
        start, end = get_start_end_dates_by_week(year, week, tz)
    elif month:
        logger.debug("Filtering by month")
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
    user: "User",
    year: Optional[int] = None,
    month: Optional[int] = None,
    week: Optional[int] = None,
    day: Optional[int] = None,
    model_str="Track",
):
    ChartRecord = apps.get_model(
        app_label="scrobbles", model_name="ChartRecord"
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
            "year": year,
            "week": week,
            "month": month,
            "day": day,
            "user": user,
        }
        chart_record["rank"] = ranks[result.scrobble_count]
        chart_record["count"] = result.scrobble_count
        if model_str == "Track":
            chart_record["track"] = result
        if model_str == "Video":
            chart_record["video"] = result
        if model_str == "Artist":
            chart_record["artist"] = result
        chart_records.append(ChartRecord(**chart_record))
    ChartRecord.objects.bulk_create(
        chart_records, ignore_conflicts=True, batch_size=500
    )


def build_yesterdays_charts_for_user(user: "User", model_str="Track") -> None:
    """Given a user calculate needed charts."""
    ChartRecord = apps.get_model(
        app_label="scrobbles", model_name="ChartRecord"
    )
    tz = pytz.timezone(settings.TIME_ZONE)
    if user and user.is_authenticated:
        tz = pytz.timezone(user.profile.timezone)
    now = timezone.now().astimezone(tz)
    yesterday = now - timedelta(days=1)
    logger.info(
        f"Generating charts for yesterday ({yesterday.date()}) for {user}"
    )

    # Always build yesterday's chart
    ChartRecord.build(
        user,
        year=yesterday.year,
        month=yesterday.month,
        day=yesterday.day,
        model_str=model_str,
    )
    now_week = now.isocalendar()[1]
    yesterday_week = now.isocalendar()[1]
    if now_week != yesterday_week:
        logger.info(
            f"New weekly charts for {yesterday.year}-{yesterday_week} for {user}"
        )
        ChartRecord.build(
            user,
            year=yesterday.year,
            month=yesterday_week,
            model_str=model_str,
        )
    # If the month has changed, build charts
    if now.month != yesterday.month:
        logger.info(
            f"New monthly charts for {yesterday.year}-{yesterday.month} for {user}"
        )
        ChartRecord.build(
            user,
            year=yesterday.year,
            month=yesterday.month,
            model_str=model_str,
        )
    # If the year has changed, build charts
    if now.year != yesterday.year:
        logger.info(f"New annual charts for {yesterday.year} for {user}")
        ChartRecord.build(user, year=yesterday.year, model_str=model_str)


def build_missing_charts_for_user(user: "User", model_str="Track") -> None:
    """"""
    ChartRecord = apps.get_model(
        app_label="scrobbles", model_name="ChartRecord"
    )
    Scrobble = apps.get_model(app_label="scrobbles", model_name="Scrobble")

    logger.info(f"Generating historical charts for {user}")
    tz = pytz.timezone(settings.TIME_ZONE)
    if user and user.is_authenticated:
        tz = pytz.timezone(user.profile.timezone)
    now = timezone.now().astimezone(tz)

    first_scrobble = (
        Scrobble.objects.filter(user=user, played_to_completion=True)
        .order_by("created")
        .first()
    )

    start_date = first_scrobble.timestamp
    days_since = (now - start_date).days

    for day_num in range(0, days_since):
        build_date = start_date + timedelta(days=day_num)
        logger.info(f"Generating chart batch for {build_date}")
        ChartRecord.build(user=user, year=build_date.year)
        ChartRecord.build(
            user=user, year=build_date.year, week=build_date.isocalendar()[1]
        )
        ChartRecord.build(
            user=user, year=build_date.year, month=build_date.month
        )
        ChartRecord.build(
            user=user,
            year=build_date.year,
            month=build_date.month,
            day=build_date.day,
        )
