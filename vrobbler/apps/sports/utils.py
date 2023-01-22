def get_round_name_from_event(event: str) -> str:
    return ' '.join(event.split(' ')[:2])


def get_players_from_event(event: str) -> list[str]:
    players = []
    event_name = get_round_name_from_event(event)
    players_list = event.split(event_name)[1:][0].split('vs')
    players.append(players_list[0].strip())
    players.append(players_list[1].strip())
    return players
