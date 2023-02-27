from rest_framework import serializers
from sports.models import (
    League,
    SportEvent,
    Round,
    Player,
    Team,
    Season,
    Sport,
)


class SportEventSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SportEvent
        fields = "__all__"


class LeagueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = League
        fields = "__all__"


class RoundSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Round
        fields = "__all__"


class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Player
        fields = "__all__"


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"


class SeasonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Season
        fields = "__all__"


class SportSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sport
        fields = "__all__"
