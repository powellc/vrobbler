from django.views import generic
from videogames.models import VideoGame


class VideoGameListView(generic.ListView):
    model = VideoGame
    paginate_by = 20


class VideoGameDetailView(generic.DetailView):
    model = VideoGame
    slug_field = "uuid"
