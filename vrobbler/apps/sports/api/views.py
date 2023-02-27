from rest_framework import permissions, viewsets
from sports.api.serializers import (
    LeagueSerializer,
    PlayerSerializer,
    RoundSerializer,
    SeasonSerializer,
    SportEventSerializer,
    SportSerializer,
    TeamSerializer,
)
from sports.models import (
    League,
    Player,
    Round,
    Season,
    Sport,
    SportEvent,
    Team,
)


class SportEventViewSet(viewsets.ModelViewSet):
    queryset = SportEvent.objects.all().order_by('-created')
    serializer_class = SportEventSerializer
    permission_classes = [permissions.IsAuthenticated]


class LeagueViewSet(viewsets.ModelViewSet):
    queryset = League.objects.all().order_by('-created')
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]


class RoundViewSet(viewsets.ModelViewSet):
    queryset = Round.objects.all().order_by('-created')
    serializer_class = RoundSerializer
    permission_classes = [permissions.IsAuthenticated]


class SportViewSet(viewsets.ModelViewSet):
    queryset = Sport.objects.all().order_by('-created')
    serializer_class = SportSerializer
    permission_classes = [permissions.IsAuthenticated]


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all().order_by('-created')
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticated]


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all().order_by('-created')
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all().order_by('-created')
    serializer_class = SeasonSerializer
    permission_classes = [permissions.IsAuthenticated]
