import logging
from typing import Optional

from howlongtobeatpy import HowLongToBeat

logger = logging.getLogger(__name__)


def lookup_game_from_hltb(name_or_id: str) -> Optional[dict]:
    """Lookup game on HowLongToBeat.com via HLtB ID or a name string and return
    the data in a dictonary mapped to our internal game fields

    """
    hltb_game = {}

    try:
        hltb_id = int(name_or_id)
    except ValueError:
        hltb_id = None

    if hltb_id:
        hltb_game = HowLongToBeat().search_from_id(hltb_id)
        logger.info(f"Found game on HLtB for ID {hltb_id}")

    if not hltb_game:
        results = HowLongToBeat().search(name_or_id)
        if not results:
            logger.warn(f"Lookup of game on HLtB failed for ID {name_or_id}")
            return

        hltb_game = results[0]
        if len(results) > 1:
            found_games = []
            for g in results:
                found_games.append(f"{g.game_name} ({g.game_id})")
            logger.info(
                f"Found more than one match {found_games}, taking {hltb_game}"
            )

    game_dict = {
        "title": hltb_game.game_name,
        "hltb_id": hltb_game.game_id,
        "main_story_time": hrs_to_secs(hltb_game.main_story),
        "main_extra_time": hrs_to_secs(hltb_game.main_extra),
        "completionist_time": hrs_to_secs(hltb_game.completionist),
        "release_year": hltb_game.release_world,
        "hltb_score": hltb_game.review_score,
        "platforms": hltb_game.profile_platforms,
        "cover_url": hltb_game.game_image_url,
    }

    return game_dict
