from datetime import datetime, timedelta
from typing import List, Optional

import pytz
from django.db.models import Count, Q, Sum
from django.utils import timezone
from music.models import Artist, Track
from scrobbles.models import Scrobble
from videos.models import Video
from vrobbler.apps.profiles.utils import now_user_timezone

NOW = timezone.now()
START_OF_TODAY = datetime.combine(NOW.date(), datetime.min.time(), NOW.tzinfo)
STARTING_DAY_OF_CURRENT_WEEK = NOW.date() - timedelta(
    days=NOW.today().isoweekday() % 7
)
STARTING_DAY_OF_CURRENT_MONTH = NOW.date().replace(day=1)
STARTING_DAY_OF_CURRENT_YEAR = NOW.date().replace(month=1, day=1)


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


def week_of_scrobbles(user=None, media: str = 'tracks') -> dict[str, int]:

    now = timezone.now()
    user_filter = Q()
    if user and user.is_authenticated:
        now = now_user_timezone(user.profile)
        user_filter = Q(user=user)

    start_of_today = datetime.combine(
        now.date(), datetime.min.time(), now.tzinfo
    )

    scrobble_day_dict = {}
    base_qs = Scrobble.objects.filter(user_filter, played_to_completion=True)

    media_filter = Q(track__isnull=False)
    if media == 'movies':
        media_filter = Q(video__video_type=Video.VideoType.MOVIE)
    if media == 'series':
        media_filter = Q(video__video_type=Video.VideoType.TV_EPISODE)

    for day in range(6, -1, -1):
        start = start_of_today - timedelta(days=day)
        end = datetime.combine(start, datetime.max.time(), now.tzinfo)
        day_of_week = start.strftime('%A')

        scrobble_day_dict[day_of_week] = base_qs.filter(
            media_filter,
            timestamp__gte=start,
            timestamp__lte=end,
            played_to_completion=True,
        ).count()

    return scrobble_day_dict


def top_tracks(
    user: "User", filter: str = "today", limit: int = 15
) -> List["Track"]:

    now = timezone.now()
    if user.is_authenticated:
        now = now_user_timezone(user.profile)

    start_of_today = datetime.combine(
        now.date(), datetime.min.time(), now.tzinfo
    )
    starting_day_of_current_week = now.date() - timedelta(
        days=now.today().isoweekday() % 7
    )
    starting_day_of_current_month = now.date().replace(day=1)
    starting_day_of_current_year = now.date().replace(month=1, day=1)

    time_filter = Q(scrobble__timestamp__gte=start_of_today)
    if filter == "week":
        time_filter = Q(scrobble__timestamp__gte=starting_day_of_current_week)
    if filter == "month":
        time_filter = Q(scrobble__timestamp__gte=starting_day_of_current_month)
    if filter == "year":
        time_filter = Q(scrobble__timestamp__gte=starting_day_of_current_year)

    return (
        Track.objects.filter(time_filter)
        .annotate(num_scrobbles=Count("scrobble", distinct=True))
        .order_by("-num_scrobbles")[:limit]
    )


def top_artists(
    user: "User", filter: str = "today", limit: int = 15
) -> List["Artist"]:
    time_filter = Q(track__scrobble__timestamp__gte=START_OF_TODAY)
    if filter == "week":
        time_filter = Q(
            track__scrobble__timestamp__gte=STARTING_DAY_OF_CURRENT_WEEK
        )
    if filter == "month":
        time_filter = Q(
            track__scrobble__timestamp__gte=STARTING_DAY_OF_CURRENT_MONTH
        )
    if filter == "year":
        time_filter = Q(
            track__scrobble__timestamp__gte=STARTING_DAY_OF_CURRENT_YEAR
        )

    return (
        Artist.objects.filter(time_filter)
        .annotate(num_scrobbles=Count("track__scrobble", distinct=True))
        .order_by("-num_scrobbles")[:limit]
    )


def artist_scrobble_count(artist_id: int, filter: str = "today") -> int:
    return Scrobble.objects.filter(track__artist=artist_id).count()
