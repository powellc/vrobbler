from trails.models import Trail

from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class TrailListView(ScrobbleableListView):
    model = Trail


class TrailDetailView(ScrobbleableDetailView):
    model = Trail
