from django.db.models import Q, Count, Sum
from typing import List, Optional
from scrobbles.models import Scrobble
from music.models import Track, Artist
from videos.models import Video

from django.utils import timezone
from datetime import datetime, timedelta


NOW = timezone.now()
START_OF_TODAY = datetime.combine(NOW.date(), datetime.min.time(), NOW.tzinfo)
STARTING_DAY_OF_CURRENT_WEEK = NOW.date() - timedelta(
    days=NOW.today().isoweekday() % 7
)
STARTING_DAY_OF_CURRENT_MONTH = NOW.date().replace(day=1)
STARTING_DAY_OF_CURRENT_YEAR = NOW.date().replace(month=1, day=1)


def scrobble_counts():
    finished_scrobbles_qs = Scrobble.objects.filter(in_progress=False)
    data = {}
    data['today'] = finished_scrobbles_qs.filter(
        timestamp__gte=START_OF_TODAY
    ).count()
    data['week'] = finished_scrobbles_qs.filter(
        timestamp__gte=STARTING_DAY_OF_CURRENT_WEEK
    ).count()
    data['month'] = finished_scrobbles_qs.filter(
        timestamp__gte=STARTING_DAY_OF_CURRENT_MONTH
    ).count()
    data['year'] = finished_scrobbles_qs.filter(
        timestamp__gte=STARTING_DAY_OF_CURRENT_YEAR
    ).count()
    data['alltime'] = finished_scrobbles_qs.count()
    return data


def week_of_scrobbles(media: str = 'tracks') -> dict[str, int]:
    scrobble_day_dict = {}
    media_filter = Q(track__isnull=False)

    for day in range(6, -1, -1):
        start = START_OF_TODAY - timedelta(days=day)
        end = datetime.combine(start, datetime.max.time(), NOW.tzinfo)
        day_of_week = start.strftime('%A')
        if media == 'movies':
            media_filter = Q(video__videotype=Video.VideoType.MOVIE)
        if media == 'series':
            media_filter = Q(video__videotype=Video.VideoType.TV_EPISODE)
        scrobble_day_dict[day_of_week] = (
            Scrobble.objects.filter(media_filter)
            .filter(
                timestamp__gte=start,
                timestamp__lte=end,
                in_progress=False,
            )
            .count()
        )

    return scrobble_day_dict


def top_tracks(filter: str = "today", limit: int = 15) -> List["Track"]:
    time_filter = Q(scrobble__timestamp__gte=START_OF_TODAY)
    if filter == "week":
        time_filter = Q(scrobble__timestamp__gte=STARTING_DAY_OF_CURRENT_WEEK)
    if filter == "month":
        time_filter = Q(scrobble__timestamp__gte=STARTING_DAY_OF_CURRENT_MONTH)
    if filter == "year":
        time_filter = Q(scrobble__timestamp__gte=STARTING_DAY_OF_CURRENT_YEAR)

    return (
        Track.objects.annotate(num_scrobbles=Count("scrobble", distinct=True))
        .filter(time_filter)
        .order_by("-num_scrobbles")[:limit]
    )


def top_artists(filter: str = "today", limit: int = 15) -> List["Artist"]:
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
        Artist.objects.annotate(
            num_scrobbles=Count("track__scrobble", distinct=True)
        )
        .filter(time_filter)
        .order_by("-num_scrobbles")[:limit]
    )


def artist_scrobble_count(artist_id: int, filter: str = "today") -> int:
    return Scrobble.objects.filter(track__artist=artist_id).count()
