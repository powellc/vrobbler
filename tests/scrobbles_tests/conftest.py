import json
import pytest


class MopidyRequest:
    def __init__(self, **kwargs):
        self.request_data = {
            "name": kwargs.get('name', "Same in the End"),
            "artist": kwargs.get("artist", "Sublime"),
            "album": kwargs.get("album", "Sublime"),
            "track_number": int(kwargs.get("track_number", 4)),
            "run_time_ticks": int(kwargs.get("run_time_ticks", 156604)),
            "run_time": int(kwargs.get("run_time", "156")),
            "playback_time_ticks": int(
                kwargs.get("playback_time_ticks", 15045)
            ),
            "musicbrainz_track_id": kwargs.get(
                "musicbrainz_track_id", "54214d63-5adf-4909-87cd-c65c37a6d558"
            ),
            "musicbrainz_album_id": kwargs.get(
                "musicbrainz_album_id", "03b864cd-7761-314c-a892-05a89ddff00d"
            ),
            "musicbrainz_artist_id": kwargs.get(
                "musicbrainz_artist_id", "95f5b748-d370-47fe-85bd-0af2dc450bc0"
            ),
            "mopidy_uri": kwargs.get(
                "mopidy_uri",
                "local:track:Sublime%20-%20Sublime/Disc%201%20-%2004%20-%20Same%20in%20the%20End.mp3",
            ),
            "status": kwargs.get("status", "resumed"),
        }

    def __eq__(self, other):
        return self.name == other.name

    @property
    def request_json(self):
        return json.dumps(self.request_data)


@pytest.fixture
def mopidy_track_request_data():
    return MopidyRequest().request_json


@pytest.fixture
def mopidy_track_diff_album_request_data(**kwargs):
    mb_album_id = "0c56c457-afe1-4679-baab-759ba8dd2a58"
    return MopidyRequest(
        album="Gold", musicbrainz_album_id=mb_album_id
    ).request_json


@pytest.fixture
def mopidy_podcast_request_data():
    mopidy_uri = "local:podcast:Up%20First/2022-01-01%20Up%20First.mp3"
    return MopidyRequest(mopidy_uri=mopidy_uri).request_json
