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
        context_data = super().get_context_data(**kwargs)

        context_data["scrobbles"] = self.object.scrobbles_for_user(
            self.request.user.id
        )
        return context_data


class VideoDetailView(generic.DetailView):
    model = Video
    slug_field = "uuid"
