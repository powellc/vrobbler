from moods.models import Mood
from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class MoodListView(ScrobbleableListView):
    model = Mood


class MoodDetailView(ScrobbleableDetailView):
    model = Mood
