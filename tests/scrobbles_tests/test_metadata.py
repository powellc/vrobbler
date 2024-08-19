import pytest

from scrobbles.dataclasses import BoardGameLogData, BoardGameScoreLogData


@pytest.mark.django_db
def test_boardgame_log_data(boardgame_scrobble):
    assert not boardgame_scrobble.geo_location
    assert boardgame_scrobble.logdata == BoardGameLogData(
        players=[
            BoardGameScoreLogData(
                user_id=1, name=None, color="Blue", score=30, win=True
            )
        ]
    )
