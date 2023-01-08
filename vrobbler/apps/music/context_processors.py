from music.models import Artist, Album


def music_lists(request):
    return {
        "artist_list": Artist.objects.all(),
        "album_list": Album.objects.all(),
    }
