import berserk
from django.conf import settings

from boardgames.models import BoardGame
from scrobbles.models import Scrobble
from django.contrib.auth import get_user_model

User = get_user_model()


def import_chess_games_for_all_users():
    client = berserk.Client(
        session=berserk.TokenSession(settings.LICHESS_API_KEY)
    )

    scrobbles_to_create = []
    for user in User.objects.filter(profile__lichess_username__isnull=False):
        games = client.games.export_by_player(user.profile.lichess_username)
        for game_dict in games:
            chess, created = BoardGame.objects.get_or_create(title="Chess")
            if created:
                chess.run_time_seconds = 1800
                chess.bggeek_id = 171
                chess.save(update_fields=["run_time_seconds", "bggeek_id"])
            scrobble = Scrobble.objects.filter(
                user_id=user.id,
                timestamp=game_dict.get("createdAt"),
                board_game_id=chess.id,
            ).first()

            if scrobble:
                continue

            log_data = {
                "variant": game_dict.get("variant"),
                "lichess_id": game_dict.get("id"),
                "rated": game_dict.get("rated"),
                "speed": game_dict.get("speed"),
                "moves": game_dict.get("moves"),
                "players": [],
            }

            chess_status = game_dict.get("status")
            chess_source = game_dict.get("source")

            winner = game_dict.get("winner")
            black_player = game_dict.get("players", {}).get("black", {})
            white_player = game_dict.get("players", {}).get("white", {})

            user_player = {
                "user_id": user.id,
                "lichess_username": user.profile.lichess_username,
                "bgg_username": user.profile.bgg_username,
                "color": "",
                "win": False,
            }
            other_player = {"name_str": "", "color": "", "win": False}

            if (
                black_player.get("user", {}).get("name", "")
                == user.profile.lichess_username
            ):
                user_player["color"] = "black"
                if "aiLevel" in white_player.keys():
                    other_player["name_str"] = "aiLevel_" + str(
                        white_player.get("aiLevel", "")
                    )
                else:
                    other_player["name_str"] = white_player.get(
                        "user", {}
                    ).get("name", "")
                    other_player["lichess_username"] = other_player["name_str"]

                other_player["color"] = "white"
                if winner == "black":
                    user_player["win"] = True
                else:
                    other_player["win"] = True
            if (
                white_player.get("user", {}).get("name", "")
                == user.profile.lichess_username
            ):
                user_player["color"] = "white"
                if "aiLevel" in black_player.keys():
                    other_player["name_str"] = "aiLevel_" + str(
                        black_player.get("aiLevel", "")
                    )
                else:
                    other_player["name_str"] = black_player.get(
                        "user", {}
                    ).get("name", "")
                    other_player["lichess_username"] = other_player["name_str"]
                other_player["color"] = "black"
                if winner == "white":
                    user_player["win"] = True
                else:
                    other_player["win"] = True

            log_data["players"].append(user_player)
            log_data["players"].append(other_player)

            scrobble_dict = {
                "media_type": Scrobble.MediaType.BOARD_GAME,
                "user_id": user.id,
                "playback_position_seconds": (
                    game_dict.get("lastMoveAt") - game_dict.get("createdAt")
                ).seconds,
                "in_progress": False,
                "played_to_completion": True,
                "timestamp": game_dict.get("createdAt"),
                "stop_timestamp": game_dict.get("lastMoveAt"),
                "board_game_id": chess.id,
                "source": "Lichess",
                "timezone": user.profile.timezone,
                "log": log_data,
            }
            scrobbles_to_create.append(Scrobble(**scrobble_dict))

    if scrobbles_to_create:
        Scrobble.objects.bulk_create(scrobbles_to_create)
    return scrobbles_to_create
