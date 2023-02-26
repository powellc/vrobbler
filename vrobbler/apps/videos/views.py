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
    slug_field = 'uuid'


class VideoDetailView(generic.DetailView):
    model = Video
    slug_field = 'uuid'
