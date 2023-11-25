from django.db.models import Count
from django.views import generic
from locations.models import GeoLocation
from scrobbles.stats import get_scrobble_count_qs


class GeoLocationListView(generic.ListView):
    model = GeoLocation
    paginate_by = 75

    def get_queryset(self):
        return super().get_queryset().filter(scrobble__user_id=self.request.user.id).order_by("-created")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["latest"] = self.get_queryset().first()
        return context_data


class GeoLocationDetailView(generic.DetailView):
    model = GeoLocation
    slug_field = "uuid"
