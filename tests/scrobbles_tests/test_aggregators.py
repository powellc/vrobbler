from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import patch

import pytest
import time_machine
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from music.aggregators import live_charts, scrobble_counts, week_of_scrobbles
from music.models import Album, Artist
from profiles.models import UserProfile
from scrobbles.models import Scrobble


def build_scrobbles(client, request_data, num=7, spacing=2):
    url = reverse("scrobbles:mopidy-webhook")
    user = get_user_model().objects.create(username="Test User")
    UserProfile.objects.create(user=user, timezone="US/Eastern")
    for i in range(num):
        client.post(url, request_data, content_type="application/json")
        s = Scrobble.objects.last()
        s.user = user
        s.timestamp = timezone.now() - timedelta(days=i * spacing)
        s.played_to_completion = True
        s.save()


@pytest.mark.django_db
@time_machine.travel(datetime(2022, 3, 4, 1, 24))
def test_scrobble_counts_data(client, mopidy_track_request_data):
    build_scrobbles(client, mopidy_track_request_data)
    user = get_user_model().objects.first()
    count_dict = scrobble_counts(user)
    assert count_dict == {
        "alltime": 7,
        "month": 2,
        "today": 1,
        "week": 3,
        "year": 7,
    }


@pytest.mark.django_db
@time_machine.travel(datetime(2022, 3, 4, 1, 24))
def test_live_charts(client, mopidy_track_request_data):
    build_scrobbles(client, mopidy_track_request_data, 7, 1)
    user = get_user_model().objects.first()

    week = week_of_scrobbles(user)
    assert list(week.values()) == [1, 1, 1, 1, 1, 1, 1]

    tops = live_charts(user)
    assert tops[0].title == "Same in the End"

    tops = live_charts(user, chart_period="week")
    assert tops[0].title == "Same in the End"

    tops = live_charts(user, chart_period="month")
    assert tops[0].title == "Same in the End"

    tops = live_charts(user, chart_period="year")
    assert tops[0].title == "Same in the End"

    tops = live_charts(user, chart_period="week", media_type="Artist")
    assert tops[0].name == "Sublime"

    tops = live_charts(user, chart_period="month", media_type="Artist")
    assert tops[0].name == "Sublime"

    tops = live_charts(user, chart_period="year", media_type="Artist")
    assert tops[0].name == "Sublime"
