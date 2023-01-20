from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from music.aggregators import scrobble_counts, week_of_scrobbles
from scrobbles.models import Scrobble


def build_scrobbles(client, request_data, num=7, spacing=2):
    url = reverse('scrobbles:mopidy-websocket')
    for i in range(num):
        client.post(url, request_data, content_type='application/json')
        s = Scrobble.objects.last()
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
