import logging

from dateutil.parser import parse
from django.conf import settings
from django.utils import timezone
from pysportsdb import TheSportsDbClient
from sports.models import Sport

logger = logging.getLogger(__name__)

API_KEY = getattr(settings, "THESPORTSDB_API_KEY", "2")
client = TheSportsDbClient(api_key=API_KEY)


def lookup_event_from_thesportsdb(event_id: str) -> dict:

    event = client.lookup_event(event_id)['events'][0]
    if not event or type(event) != dict:
        return {}
    league = {}  # client.lookup_league(league_id=event.get('idLeague'))
    event_type = "Game"
    sport, _created = Sport.objects.get_or_create(
        thesportsdb_id=event.get('strSport')
    )

    data_dict = {
        "EventId": event_id,
        "ItemType": sport.default_event_type,
        "Name": event.get('strEvent'),
        "AltName": event.get('strEventAlternate'),
        "Start": parse(event.get('strTimestamp')),
        "Provider_thesportsdb": event.get('idEvent'),
        "RunTime": sport.default_event_run_time,
        "RunTimeTicks": sport.default_event_run_time_ticks,
        "Sport": event.get('strSport'),
        "Season": event.get('strSeason'),
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
        "Source": "Vrobbler",
    }

    return data_dict
