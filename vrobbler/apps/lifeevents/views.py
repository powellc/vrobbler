from django.views import generic
from lifeevents.models import LifeEvent


class LifeEventListView(generic.ListView):
    model = LifeEvent
    paginate_by = 20


class LifeEventDetailView(generic.DetailView):
    model = LifeEvent
    slug_field = "uuid"
