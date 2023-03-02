from django.views import generic
from sports.models import SportEvent


class SportEventListView(generic.ListView):
    model = SportEvent
    paginate_by = 50


class SportEventDetailView(generic.DetailView):
    model = SportEvent
    slug_field = 'uuid'
