from datetime import datetime, timedelta
from unittest.mock import patch
from django.utils import timezone

import pytest
import time_machine
from django.urls import reverse
from music.models import Track
from podcasts.models import PodcastEpisode
from scrobbles.models import Scrobble


@pytest.mark.django_db
def test_get_not_allowed_from_mopidy(client, valid_auth_token):
    url = reverse("scrobbles:mopidy-webhook")
    headers = {"Authorization": f"Token {valid_auth_token}"}
    response = client.get(url, headers=headers)
    assert response.status_code == 405


@pytest.mark.django_db
def test_bad_mopidy_request_data(client, valid_auth_token):
    url = reverse("scrobbles:mopidy-webhook")
    headers = {"Authorization": f"Token {valid_auth_token}"}
    response = client.post(url, headers)
    assert response.status_code == 400
    assert (
        response.data["detail"]
        == "JSON parse error - Expecting value: line 1 column 1 (char 0)"
    )


@pytest.mark.django_db
def test_scrobble_mopidy_track(
    client, mopidy_track, valid_auth_token
):
    url = reverse("scrobbles:mopidy-webhook")
    headers = {"Authorization": f"Token {valid_auth_token}"}

    # Start new scrobble
    seconds = 1
    scrobble_id = 1
    with time_machine.travel(datetime(2024, 1, 14, 12, 0, seconds)):
        mopidy_track.request_data["playback_time_ticks"] = seconds * 1000
        response = client.post(
            url,
            mopidy_track.request_json,
            content_type="application/json",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.data == {"scrobble_id": scrobble_id}

        scrobble = Scrobble.objects.get(id=1)
        assert scrobble.media_obj.__class__ == Track
        assert scrobble.media_obj.title == "Same in the End"

    # Continue existingscrobble
    seconds = 58
    scrobble_id = 1
    with time_machine.travel(datetime(2024, 1, 14, 12, 0, seconds)):
        mopidy_track.request_data["playback_time_ticks"] = seconds * 1000
        response = client.post(
            url,
            mopidy_track.request_json,
            content_type="application/json",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.data == {"scrobble_id": scrobble_id}

        scrobble = Scrobble.objects.get(id=1)
        assert scrobble.media_obj.__class__ == Track
        assert scrobble.media_obj.title == "Same in the End"

    # Continue new scrobble
    seconds = 61
    scrobble_id = 2
    with time_machine.travel(datetime(2024, 1, 14, 12, 1, seconds)):
        mopidy_track.request_data["playback_time_ticks"] = seconds * 1000
        response = client.post(
            url,
            mopidy_track.request_json,
            content_type="application/json",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.data == {"scrobble_id": scrobble_id}

        scrobble = Scrobble.objects.get(id=1)
        assert scrobble.media_obj.__class__ == Track
        assert scrobble.media_obj.title == "Same in the End"


@pytest.mark.skip(reason="Allmusic API is unstable")
@pytest.mark.django_db
def test_scrobble_mopidy_same_track_different_album(
    client,
    mopidy_track,
    mopidy_track_diff_album_request_data,
    valid_auth_token,
):
    url = reverse("scrobbles:mopidy-webhook")
    headers = {"Authorization": f"Token {valid_auth_token}"}
    response = client.post(
        url,
        mopidy_track.request_data,
        content_type="application/json",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.data == {"scrobble_id": 1}
    scrobble = Scrobble.objects.last()
    assert scrobble.media_obj.album.name == "Sublime"

    response = client.post(
        url,
        mopidy_track_diff_album_request_data,
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.data == {"scrobble_id": 2}
    scrobble = Scrobble.objects.last()
    assert scrobble.media_obj.__class__ == Track
    assert scrobble.media_obj.album.name == "Gold"
    assert scrobble.media_obj.title == "Same in the End"


@pytest.mark.django_db
def test_scrobble_mopidy_podcast(
    client, mopidy_podcast_request_data, valid_auth_token
):
    url = reverse("scrobbles:mopidy-webhook")
    headers = {"Authorization": f"Token {valid_auth_token}"}
    response = client.post(
        url,
        mopidy_podcast_request_data,
        content_type="application/json",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.data == {"scrobble_id": 1}

    scrobble = Scrobble.objects.get(id=1)
    assert scrobble.media_obj.__class__ == PodcastEpisode
    assert scrobble.media_obj.title == "Up First"


@pytest.mark.django_db
@patch("music.utils.lookup_artist_from_mb", return_value={})
@patch("music.utils.lookup_album_dict_from_mb", return_value={"year": "1999", "mb_group_id": 1})
@patch("music.utils.lookup_track_from_mb", return_value={})
@patch("music.models.lookup_artist_from_tadb", return_value={})
@patch("music.models.lookup_album_from_tadb", return_value={"year": "1999"})
@patch("music.models.Album.fetch_artwork", return_value=None)
@patch("music.models.Album.scrape_allmusic", return_value=None)
def test_scrobble_jellyfin_track(
        mock_lookup_artist,
        mock_lookup_album,
        mock_lookup_track,
        mock_lookup_artist_tadb,
        mock_lookup_album_tadb,
        mock_fetch_artwork,
        mock_scrape_allmusic,
        client,
        jellyfin_track,
        valid_auth_token,
):
    url = reverse("scrobbles:jellyfin-webhook")
    headers = {"Authorization": f"Token {valid_auth_token}"}

    with time_machine.travel(datetime(2024, 1, 14, 12, 00, 1)):
        jellyfin_track.request_data["UtcTimestamp"] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        response = client.post(
            url,
            jellyfin_track.request_json,
            content_type="application/json",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.data == {"scrobble_id": 1}

        scrobble = Scrobble.objects.get(id=1)
        assert scrobble.media_obj.__class__ == Track
        assert scrobble.media_obj.title == "Emotion"

    with time_machine.travel(datetime(2024, 1, 14, 12, 0, 58)):
        jellyfin_track.request_data["UtcTimestamp"] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        response = client.post(
            url,
            jellyfin_track.request_json,
            content_type="application/json",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.data == {"scrobble_id": 1}

        scrobble = Scrobble.objects.get(id=1)
        assert scrobble.media_obj.__class__ == Track
        assert scrobble.media_obj.title == "Emotion"

    with time_machine.travel(datetime(2024, 1, 14, 12, 1, 1)):
        jellyfin_track.request_data["UtcTimestamp"] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        response = client.post(
            url,
            jellyfin_track.request_json,
            content_type="application/json",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.data == {"scrobble_id": 2}

        scrobble = Scrobble.objects.get(id=1)
        assert scrobble.media_obj.__class__ == Track
        assert scrobble.media_obj.title == "Emotion"
