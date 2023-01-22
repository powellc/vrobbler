from django.contrib import admin

from sports.models import (
    League,
    Player,
    Round,
    Season,
    Sport,
    SportEvent,
    Team,
)

from scrobbles.admin import ScrobbleInline


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    ordering = ("name",)


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "abbreviation_str")
    ordering = ("name",)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "league", "team")
    ordering = ("name",)


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "league")
    ordering = ("name",)


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "season")
    ordering = ("name",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "league")
    ordering = ("name",)


@admin.register(SportEvent)
class SportEventAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "title",
        "event_type",
        "start",
        "comp_str",
        "round",
    )
    list_filter = ("round__season", "home_team", "away_team")
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]

    def comp_str(self, obj):
        if obj.home_team:
            return f'{obj.away_team} @ {obj.home_team}'
        if obj.player_one:
            return f'{obj.player_one} v {obj.player_two}'
