from django.views import generic
from webpages.models import WebPage


class WebPageListView(generic.ListView):
    model = WebPage
    paginate_by = 20


class WebPageDetailView(generic.DetailView):
    model = WebPage
    slug_field = "uuid"
