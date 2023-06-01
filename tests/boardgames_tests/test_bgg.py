from boardgames.bgg import (
    take_first,
    lookup_boardgame_id_from_bgg,
    lookup_boardgame_from_bgg,
)


def test_take_first():
    assert take_first([]) == ""

    assert take_first(["a", "b"]) == "a"


def test_lookup_boardgame_id_from_bgg():
    bgg_id = lookup_boardgame_id_from_bgg("Cosmic Encounter")
    assert bgg_id == "15"

    bgg_id = lookup_boardgame_id_from_bgg("Comedy Encounter")
    assert bgg_id == None


def test_lookup_boardgame_from_bgg():
    bgg_result = lookup_boardgame_from_bgg(15)
    assert bgg_result.get("bggeek_id") == 15

    bgg_result = lookup_boardgame_from_bgg("Cosmic Encounter")
    assert bgg_result.get("bggeek_id") == "15"
