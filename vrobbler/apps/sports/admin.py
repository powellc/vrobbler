from django.contrib import admin

from sports.models import League, SportEvent, Team

from scrobbles.admin import ScrobbleInline


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name", "abbreviation_str")
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
        "home_team",
        "away_team",
        "season",
    )
    list_filter = ("season", "home_team", "away_team")
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
