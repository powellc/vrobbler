from videos.sources.imdb import lookup_video_from_imdb


def test_lookup_imdb():
    metadata = lookup_video_from_imdb("8946378")
    assert metadata.title == "Knives Out"
