import logging

from dateutil.parser import parse
from django.conf import settings
from django.utils import timezone
from pysportsdb import TheSportsDbClient
from sports.models import SportEvent

logger = logging.getLogger(__name__)

API_KEY = getattr(settings, "THESPORTSDB_API_KEY", "2")
client = TheSportsDbClient(api_key=API_KEY)


def lookup_event_from_thesportsdb(event_id: str) -> dict:

    event = client.lookup_event(event_id)['events'][0]
    league = {}  # client.lookup_league(league_id=event.get('idLeague'))
    event_type = SportEvent.Type.GAME
    run_time_seconds = 11700
    run_time_ticks = run_time_seconds * 1000

    data_dict = {
        "ItemType": event_type,
        "Name": event.get('strEventAlternate'),
        "Start": parse(event.get('strTimestamp')),
        "Provider_thesportsdb": event.get('idEvent'),
        "RunTime": run_time_seconds,
        "RunTimeTicks": run_time_ticks,
        "LeagueId": event.get('idLeague'),
        "LeagueName": event.get('strLeague'),
        "HomeTeamId": event.get('idHomeTeam'),
        "HomeTeamName": event.get('strHomeTeam'),
        "AwayTeamId": event.get('idAwayTeam'),
        "AwayTeamName": event.get('strAwayTeam'),
        "RoundId": event.get('intRound'),
        "PlaybackPositionTicks": None,
        "PlaybackPosition": None,
        "UtcTimestamp": timezone.now().strftime('%Y-%m-%d %H:%M:%S.%f%z'),
        "IsPaused": False,
        "PlayedToCompletion": False,
    }

    return data_dict
