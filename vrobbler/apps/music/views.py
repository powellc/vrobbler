from django.db.models import Count
from django.views import generic
from music.models import Album, Artist, Track
from scrobbles.models import ChartRecord
from scrobbles.stats import get_scrobble_count_qs

from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class TrackListView(ScrobbleableListView):
    model = Track


class TrackDetailView(ScrobbleableDetailView):
    model = Track

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["charts"] = ChartRecord.objects.filter(
            track=self.object, rank__in=[1, 2, 3]
        )
        return context_data


class ArtistListView(generic.ListView):
    model = Artist
    paginate_by = 100

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(scrobble_count=Count("track__scrobble"))
            .order_by("-scrobble_count")
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(
            object_list=object_list, **kwargs
        )
        context_data["view"] = self.request.GET.get("view")
        return context_data


class ArtistDetailView(generic.DetailView):
    model = Artist
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        artist = context_data["object"]
        rank = 1
        tracks_ranked = []
        scrobbles = artist.tracks.first().scrobble_count
        for track in artist.tracks:
            if scrobbles > track.scrobble_count:
                rank += 1
            tracks_ranked.append((rank, track))
            scrobbles = track.scrobble_count

        context_data["tracks_ranked"] = tracks_ranked
        context_data["charts"] = ChartRecord.objects.filter(
            artist=self.object, rank__in=[1, 2, 3]
        )
        return context_data


class AlbumListView(generic.ListView):
    model = Album

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(scrobble_count=Count("track__scrobble"))
            .order_by("-scrobble_count")
        )


class AlbumDetailView(generic.DetailView):
    model = Album
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # context_data['charts'] = ChartRecord.objects.filter(
        #    track__album=self.object, rank__in=[1, 2, 3]
        # )
        return context_data
