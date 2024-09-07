from bricksets.models import BrickSet
from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class BrickSetListView(ScrobbleableListView):
    model = BrickSet


class BrickSetDetailView(ScrobbleableDetailView):
    model = BrickSet
