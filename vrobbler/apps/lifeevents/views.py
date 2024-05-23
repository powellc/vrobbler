from django.views import generic
from lifeevents.models import LifeEvent


class EventListView(generic.ListView):
    model = LifeEvent
    paginate_by = 20


class EventDetailView(generic.DetailView):
    model = LifeEvent
    slug_field = "uuid"
