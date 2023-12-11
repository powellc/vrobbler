from django.db.models import Count
from django.views import generic
from webpages.models import WebPage


class WebPageListView(generic.ListView):
    model = WebPage
    paginate_by = 20

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(scrobble_count=Count("scrobble"))
            .order_by("-scrobble_count")
        )


class WebPageDetailView(generic.DetailView):
    model = WebPage
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        user = self.request.user
        context_data = super().get_context_data(**kwargs)
        context_data["scrobbles"] = self.object.scrobbles(user)
        return context_data
