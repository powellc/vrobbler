import pytest
from videos.sources.youtube import lookup_video_from_youtube


@pytest.mark.django_db
def test_lookup_youtube_id():
    metadata = lookup_video_from_youtube("RZxs9pAv99Y")
    assert metadata.title == "No Pun Included's Board Game of the Year 2024"
