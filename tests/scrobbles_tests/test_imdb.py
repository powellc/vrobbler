import pytest

from vrobbler.apps.scrobbles.imdb import lookup_video_from_imdb


@pytest.mark.skip(reason="Need to sort out third party API testing")
def test_lookup_imdb_bad_id(caplog):
    data = lookup_video_from_imdb('3409324')
    assert data is None
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].msg == "IMDB ID should begin with 'tt' 3409324"
