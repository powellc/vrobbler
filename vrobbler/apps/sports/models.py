import logging
from typing import Dict
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}


class League(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    logo = models.ImageField(upload_to="sports/league-logos/", **BNULL)
    abbreviation_str = models.CharField(max_length=10, **BNULL)
    thesportsdb_id = models.IntegerField(**BNULL)

    def __str__(self):
        return self.name

    @property
    def abbreviation(self):
        return self.abbreviation_str


class Team(TimeStampedModel):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    league = models.ForeignKey(League, on_delete=models.DO_NOTHING, **BNULL)
    thesportsdb_id = models.IntegerField(**BNULL)

    def __str__(self):
        return self.name


class SportEvent(ScrobblableMixin):
    RESUME_LIMIT = getattr(settings, 'SPORT_RESUME_LIMIT', (12 * 60) * 60)
    COMPLETION_PERCENT = getattr(settings, 'SPORT_COMPLETION_PERCENT', 90)

    class Type(models.TextChoices):
        UNKNOWN = 'UK', _('Unknown')
        GAME = 'GA', _('Game')
        MATCH = 'MA', _('Match')
        MEET = 'ME', _('Meet')

    event_type = models.CharField(
        max_length=2,
        choices=Type.choices,
        default=Type.UNKNOWN,
    )
    league = models.ForeignKey(League, on_delete=models.DO_NOTHING, **BNULL)
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
    season = models.CharField(max_length=255, **BNULL)

    def __str__(self):
        return f"{self.start.date()} - {self.league.abbreviation} - {self.home_team} v {self.away_team}"

    def get_absolute_url(self):
        return reverse("sports:event_detail", kwargs={'slug': self.uuid})

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> "Event":
        """Given a data dict from Jellyfin, does the heavy lifting of looking up
        the video and, if need, TV Series, creating both if they don't yet
        exist.

        """
        league_dict = {
            "abbreviation_str": data_dict.get("LeagueName", ""),
            "thesportsdb_id": data_dict.get("LeagueId", ""),
        }
        league, _created = League.objects.get_or_create(**league_dict)

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
            "title": data_dict.get("Name"),
            "event_type": data_dict.get("ItemType"),
            "home_team": home_team,
            "away_team": away_team,
            "start": data_dict['Start'],
            "league": league,
            "run_time_ticks": data_dict.get("RunTimeTicks"),
            "run_time": data_dict.get("RunTime", ""),
        }
        event, _created = cls.objects.get_or_create(**event_dict)

        return event
