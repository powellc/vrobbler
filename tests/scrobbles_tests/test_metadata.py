import pytest

from scrobbles.dataclasses import BoardGameLogData, BoardGameScoreLogData


@pytest.mark.django_db
def test_boardgame_log_data(boardgame_scrobble):
    assert not boardgame_scrobble.geo_location
    assert boardgame_scrobble.logdata == BoardGameLogData(
        players=[
            BoardGameScoreLogData(
                user_id=1,
                name_str="",
                bgg_username="",
                color="Blue",
                character=None,
                team=None,
                score=30,
                win=True,
                new=None,
            )
        ],
        location=None,
        geo_location_id=None,
        difficulty=None,
        solo=None,
        two_handed=None,
    )
    assert len(boardgame_scrobble.logdata.players) == 1
    assert boardgame_scrobble.logdata.players[0].user.id == 1
    assert boardgame_scrobble.logdata.players[0].name == "Test"
