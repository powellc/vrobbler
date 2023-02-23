import logging
from typing import Dict
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin
from sports.utils import get_players_from_event, get_round_name_from_event

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class SportEventType(models.TextChoices):
    UNKNOWN = 'UK', _('Event')
    GAME = 'GA', _('Game')
    RACE = 'RA', _('Race')
    MATCH = 'MA', _('Match')


class TheSportsDbMixin(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    thesportsdb_id = models.CharField(max_length=255, **BNULL)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Sport(TheSportsDbMixin):
    default_event_run_time = models.IntegerField(**BNULL)
    default_event_type = models.CharField(
        max_length=2,
        choices=SportEventType.choices,
        default=SportEventType.UNKNOWN,
    )

    # TODO Add these to the default run_time for Football
    # run_time_seconds = 11700
    # run_time_ticks = run_time_seconds * 1000
    @property
    def default_event_run_time_ticks(self):
        default_run_time = getattr(
            settings, 'DEFAULT_EVENT_RUNTIME_SECONDS', 14400
        )
        if self.default_event_run_time:
            default_run_time = self.default_event_run_time
        return default_run_time * 1000


class League(TheSportsDbMixin):
    logo = models.ImageField(upload_to="sports/league-logos/", **BNULL)
    abbreviation_str = models.CharField(max_length=10, **BNULL)
    sport = models.ForeignKey(Sport, on_delete=models.DO_NOTHING, **BNULL)

    @property
    def abbreviation(self):
        return self.abbreviation_str


class Season(TheSportsDbMixin):
    league = models.ForeignKey(League, on_delete=models.DO_NOTHING, **BNULL)

    def __str__(self):
        return f'{self.name} season of {self.league}'


class Team(TheSportsDbMixin):
    league = models.ForeignKey(League, on_delete=models.DO_NOTHING, **BNULL)


class Player(TheSportsDbMixin):
    league = models.ForeignKey(League, on_delete=models.DO_NOTHING, **BNULL)
    team = models.ForeignKey(Team, on_delete=models.DO_NOTHING, **BNULL)


class Round(TheSportsDbMixin):
    season = models.ForeignKey(Season, on_delete=models.DO_NOTHING, **BNULL)

    def __str__(self):
        return f'{self.name} of {self.season}'


class SportEvent(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, 'SPORT_COMPLETION_PERCENT', 90)

    thesportsdb_id = models.CharField(max_length=255, **BNULL)
    event_type = models.CharField(
        max_length=2,
        choices=SportEventType.choices,
        default=SportEventType.UNKNOWN,
    )
    round = models.ForeignKey(Round, on_delete=models.DO_NOTHING, **BNULL)
    start = models.DateTimeField(**BNULL)
    home_team = models.ForeignKey(
        Team,
        on_delete=models.DO_NOTHING,
        related_name='home_event_set',
        **BNULL,
    )
    away_team = models.ForeignKey(
        Team,
        on_delete=models.DO_NOTHING,
        related_name='away_event_set',
        **BNULL,
    )
    player_one = models.ForeignKey(
        Player,
        on_delete=models.DO_NOTHING,
        related_name='player_one_set',
        **BNULL,
    )
    player_two = models.ForeignKey(
        Player,
        on_delete=models.DO_NOTHING,
        related_name='player_two_set',
        **BNULL,
    )

    def __str__(self):
        return f"{self.start.date()} - {self.round} - {self.home_team} v {self.away_team}"

    def get_absolute_url(self):
        return reverse("sports:event_detail", kwargs={'slug': self.uuid})

    @property
    def subtitle(self):
        return self.round.season.league

    @property
    def sportsdb_link(self):
        return f"https://thesportsdb.com/event/{self.thesportsdb_id}"

    @property
    def info_link(self):
        return self.sportsdb_link

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> "Event":
        """Given a data dict from Jellyfin, does the heavy lifting of looking up
        the video and, if need, TV Series, creating both if they don't yet
        exist.

        """
        # Find or create our Sport
        sid = data_dict.get("Sport")
        sport, s_created = Sport.objects.get_or_create(thesportsdb_id=sid)
        if s_created:
            sport.name = sid
            sport.save(update_fields=['name'])

        # Find or create our League
        lid = data_dict.get("LeagueId")
        league, l_created = League.objects.get_or_create(
            thesportsdb_id=lid, sport=sport
        )
        if l_created:
            league.sport = sport
            league.name = data_dict.get("LeagueName", "")
            league.save(update_fields=['sport', 'name'])

        # Find or create our Season
        seid = data_dict.get('Season')
        season, se_created = Season.objects.get_or_create(
            thesportsdb_id=seid, league=league
        )
        if se_created:
            season.name = seid
            season.save(update_fields=['name'])

        # Find or create our Round
        rid = data_dict.get('RoundId')
        round, r_created = Round.objects.get_or_create(
            thesportsdb_id=rid, season=season
        )
        if r_created:
            round.season = season
            round.save(update_fields=['season'])

        # Set some special data for Tennis
        player_one = None
        player_two = None
        if data_dict.get('Sport') == 'Tennis':
            event_name = data_dict.get('Name', '')
            if not round.name:
                round.name = get_round_name_from_event(event_name)
                round.save(update_fields=['name'])

            players_list = get_players_from_event(event_name)
            player_one = Player.objects.filter(
                name__icontains=players_list[0]
            ).first()
            if not player_one:
                player_one = Player.objects.create(name=players_list[0])
            player_two = Player.objects.filter(
                name__icontains=players_list[1]
            ).first()
            if not player_two:
                player_two = Player.objects.create(name=players_list[1])

        home_team = None
        away_team = None
        if data_dict.get("HomeTeamName"):
            home_team_dict = {
                "name": data_dict.get("HomeTeamName", ""),
                "thesportsdb_id": data_dict.get("HomeTeamId", ""),
                "league": league,
            }
            home_team, _created = Team.objects.get_or_create(**home_team_dict)

            away_team_dict = {
                "name": data_dict.get("AwayTeamName", ""),
                "thesportsdb_id": data_dict.get("AwayTeamId", ""),
                "league": league,
            }
            away_team, _created = Team.objects.get_or_create(**away_team_dict)

        event_dict = {
            "thesportsdb_id": data_dict.get("EventId"),
            "title": data_dict.get("Name"),
            "event_type": sport.default_event_type,
            "home_team": home_team,
            "away_team": away_team,
            "player_one": player_one,
            "player_two": player_two,
            "start": data_dict['Start'],
            "round": round,
            "run_time_ticks": data_dict.get("RunTimeTicks"),
            "run_time": data_dict.get("RunTime", ""),
        }
        event, _created = cls.objects.get_or_create(**event_dict)

        return event
