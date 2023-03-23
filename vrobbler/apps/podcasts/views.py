from django.views import generic
from podcasts.models import Podcast


class PodcastListView(generic.ListView):
    model = Podcast
    paginate_by = 20


class PodcastDetailView(generic.DetailView):
    model = Podcast
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        user = self.request.user
        context_data = super().get_context_data(**kwargs)
        context_data["scrobbles"] = self.object.scrobbles(user)
        return context_data
