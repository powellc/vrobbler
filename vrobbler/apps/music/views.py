from datetime import timedelta
from django.utils import timezone
from django.views import generic
from music.models import Album, Artist, Track
from scrobbles.models import ChartRecord
from scrobbles.stats import get_scrobble_count_qs


class TrackListView(generic.ListView):
    model = Track
    paginate_by = 200

    def get_queryset(self):
        return get_scrobble_count_qs(user=self.request.user).order_by(
            "-scrobble_count"
        )


class TrackDetailView(generic.DetailView):
    model = Track
    slug_field = 'uuid'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data['charts'] = ChartRecord.objects.filter(
            track=self.object, rank__in=[1, 2, 3]
        )
        return context_data


class ArtistListView(generic.ListView):
    model = Artist
    paginate_by = 100

    def get_queryset(self):
        return super().get_queryset().order_by("name")

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(
            object_list=object_list, **kwargs
        )
        context_data['view'] = self.request.GET.get('view')
        return context_data


class ArtistDetailView(generic.DetailView):
    model = Artist
    slug_field = 'uuid'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['charts'] = ChartRecord.objects.filter(
            artist=self.object, rank__in=[1, 2, 3]
        )
        return context_data


class AlbumListView(generic.ListView):
    model = Album
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().order_by("name")

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(
            object_list=object_list, **kwargs
        )
        context_data['view'] = self.request.GET.get('view')
        return context_data


class AlbumDetailView(generic.DetailView):
    model = Album
    slug_field = 'uuid'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # context_data['charts'] = ChartRecord.objects.filter(
        #    track__album=self.object, rank__in=[1, 2, 3]
        # )
        return context_data
