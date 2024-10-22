from beers.models import Beer

from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class BeerListView(ScrobbleableListView):
    model = Beer


class BeerDetailView(ScrobbleableDetailView):
    model = Beer
