from django.views import generic
from music.models import Track, Artist, Album
from scrobbles.stats import get_scrobble_count_qs


class TrackListView(generic.ListView):
    model = Track

    def get_queryset(self):
        return get_scrobble_count_qs(user=self.request.user).order_by(
            "-scrobble_count"
        )


class TrackDetailView(generic.DetailView):
    model = Track
    slug_field = 'uuid'


class ArtistListView(generic.ListView):
    model = Artist

    def get_queryset(self):
        return super().get_queryset().order_by("name")


class ArtistDetailView(generic.DetailView):
    model = Artist
    slug_field = 'uuid'


class AlbumListView(generic.ListView):
    model = Album
