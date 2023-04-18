from django.views import generic
from boardgames.models import BoardGame, BoardGamePublisher


class BoardGameListView(generic.ListView):
    model = BoardGame
    paginate_by = 20


class BoardGameDetailView(generic.DetailView):
    model = BoardGame
    slug_field = "uuid"


class BoardGamePublisherDetailView(generic.DetailView):
    model = BoardGamePublisher
    slug_field = "uuid"
