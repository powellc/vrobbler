import json
import pytest

from django.urls import reverse

from scrobbles.models import Scrobble
from music.models import Track
from podcasts.models import Episode


@pytest.mark.django_db
def test_get_not_allowed_from_mopidy(client, valid_auth_token):
    url = reverse('scrobbles:mopidy-webhook')
    headers = {'Authorization': f'Token {valid_auth_token}'}
    response = client.get(url, headers=headers)
    assert response.status_code == 405


@pytest.mark.django_db
def test_bad_mopidy_request_data(client, valid_auth_token):
    url = reverse('scrobbles:mopidy-webhook')
    headers = {'Authorization': f'Token {valid_auth_token}'}
    response = client.post(url, headers)
    assert response.status_code == 400
    assert (
        response.data['detail']
        == 'JSON parse error - Expecting value: line 1 column 1 (char 0)'
    )


@pytest.mark.django_db
def test_scrobble_mopidy_track(
    client, mopidy_track_request_data, valid_auth_token
):
    url = reverse('scrobbles:mopidy-webhook')
    headers = {'Authorization': f'Token {valid_auth_token}'}
    response = client.post(
        url,
        mopidy_track_request_data,
        content_type='application/json',
        headers=headers,
    )
    assert response.status_code == 200
    assert response.data == {'scrobble_id': 1}

    scrobble = Scrobble.objects.get(id=1)
    assert scrobble.media_obj.__class__ == Track
    assert scrobble.media_obj.title == "Same in the End"


@pytest.mark.django_db
def test_scrobble_mopidy_same_track_different_album(
    client,
    mopidy_track_request_data,
    mopidy_track_diff_album_request_data,
    valid_auth_token,
):
    url = reverse('scrobbles:mopidy-webhook')
    headers = {'Authorization': f'Token {valid_auth_token}'}
    response = client.post(
        url,
        mopidy_track_request_data,
        content_type='application/json',
        headers=headers,
    )
    assert response.status_code == 200
    assert response.data == {'scrobble_id': 1}
    scrobble = Scrobble.objects.get(id=1)
    assert scrobble.media_obj.album.name == "Sublime"

    response = client.post(
        url,
        mopidy_track_diff_album_request_data,
        content_type='application/json',
    )

    scrobble = Scrobble.objects.get(id=2)
    assert scrobble.media_obj.__class__ == Track
    assert scrobble.media_obj.album.name == "Gold"
    assert scrobble.media_obj.title == "Same in the End"


@pytest.mark.django_db
def test_scrobble_mopidy_podcast(
    client, mopidy_podcast_request_data, valid_auth_token
):
    url = reverse('scrobbles:mopidy-webhook')
    headers = {'Authorization': f'Token {valid_auth_token}'}
    response = client.post(
        url,
        mopidy_podcast_request_data,
        content_type='application/json',
        headers=headers,
    )
    assert response.status_code == 200
    assert response.data == {'scrobble_id': 1}

    scrobble = Scrobble.objects.get(id=1)
    assert scrobble.media_obj.__class__ == Episode
    assert scrobble.media_obj.title == "Up First"
