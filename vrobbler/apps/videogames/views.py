from django.views import generic
from videogames.models import VideoGame, VideoGamePlatform


class VideoGameListView(generic.ListView):
    model = VideoGame
    paginate_by = 20


class VideoGameDetailView(generic.DetailView):
    model = VideoGame
    slug_field = "uuid"


class VideoGamePlatformDetailView(generic.DetailView):
    model = VideoGamePlatform
    slug_field = "uuid"
