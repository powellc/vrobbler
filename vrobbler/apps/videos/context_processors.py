from videos.models import Video, Series


def video_lists(request):
    return {
        "movie_list": Video.objects.filter(video_type=Video.VideoType.MOVIE),
        "series_list": Series.objects.all(),
    }
