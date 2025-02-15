from django.contrib import admin
from podcasts.models import PodcastEpisode, Podcast, Producer
from scrobbles.admin import ScrobbleInline


@admin.register(Producer)
class ProducerAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ("name",)
    ordering = ("name",)


@admin.register(Podcast)
class PodcastAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "name",
        "producer",
        "active",
    )
    ordering = ("name",)


@admin.register(PodcastEpisode)
class PodcastEpisodeAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = (
        "title",
        "podcast",
    )
    list_filter = ("podcast",)
    ordering = ("-created",)
    inlines = [
        ScrobbleInline,
    ]
