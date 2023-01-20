from datetime import timedelta
from django.contrib.auth import get_user_model

import pytest
from django.urls import reverse
from django.utils import timezone
from music.aggregators import scrobble_counts, top_tracks, week_of_scrobbles
from scrobbles.models import Scrobble
from profiles.models import UserProfile


def build_scrobbles(client, request_data, num=7, spacing=2):
    url = reverse('scrobbles:mopidy-websocket')
    user = get_user_model().objects.create(username='Test User')
    UserProfile.objects.create(user=user, timezone='US/Eastern')
    for i in range(num):
        client.post(url, request_data, content_type='application/json')
        s = Scrobble.objects.last()
        s.user = user
        s.timestamp = timezone.now() - timedelta(days=i * spacing)
        s.played_to_completion = True
        s.save()


@pytest.mark.django_db
def test_scrobble_counts_data(client, mopidy_track_request_data):
    build_scrobbles(client, mopidy_track_request_data)
    count_dict = scrobble_counts()
    assert count_dict == {
        'alltime': 7,
        'month': 7,
        'today': 1,
        'week': 2,
        'year': 7,
    }


@pytest.mark.django_db
def test_week_of_scrobbles_data(client, mopidy_track_request_data):
    build_scrobbles(client, mopidy_track_request_data, 7, 1)
    week = week_of_scrobbles()
    assert list(week.values()) == [1, 1, 1, 1, 1, 1, 1]


@pytest.mark.django_db
def test_top_tracks_by_day(client, mopidy_track_request_data):
    build_scrobbles(client, mopidy_track_request_data, 7, 1)
    user = get_user_model().objects.first()
    tops = top_tracks(user)
    assert tops[0].title == "Same in the End"
