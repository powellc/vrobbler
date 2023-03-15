from django.views import generic
from videos.models import Series, Video

# class VideoIndexView():


class MovieListView(generic.ListView):
    model = Video
    template_name = "videos/movie_list.html"

    def get_queryset(self):
        return Video.objects.filter(video_type=Video.VideoType.MOVIE)


class SeriesListView(generic.ListView):
    model = Series


class SeriesDetailView(generic.DetailView):
    model = Series
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        user_id = self.request.user.id
        context_data = super().get_context_data(**kwargs)

        context_data["scrobbles"] = self.object.scrobbles_for_user(user_id)
        next_episode_id = self.object.last_scrobbled_episode(
            user_id
        ).next_imdb_id
        if self.object.is_episode_playing(user_id):
            next_episode_id = None
        context_data["next_episode_id"] = next_episode_id
        return context_data


class VideoDetailView(generic.DetailView):
    model = Video
    slug_field = "uuid"
