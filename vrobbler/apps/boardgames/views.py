from django.views import generic
from boardgames.models import BoardGame, BoardGamePublisher
from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class BoardGameListView(ScrobbleableListView):
    model = BoardGame


class BoardGameDetailView(ScrobbleableDetailView):
    model = BoardGame


class BoardGamePublisherDetailView(generic.DetailView):
    model = BoardGamePublisher
    slug_field = "uuid"
