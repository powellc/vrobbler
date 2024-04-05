import pytest
from vrobbler.apps.podcasts.scrapers import scrape_data_from_google_podcasts

expected_desc_snippet = (
    "NPR's Up First is the news you need to start your day. "
)

expected_img_url = "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcR1F0CfR24RR6sme531yIkCrnK4zzmo97jeualO5drVPKG6oCk"
expected_google_url = "https://podcasts.google.com/feed/aHR0cHM6Ly9mZWVkcy5ucHIub3JnLzUxMDMxOC9wb2RjYXN0LnhtbA"


@pytest.mark.skip("Google Podcasts is gone")
def test_get_not_allowed_from_mopidy():
    query = "Up First"
    result_dict = scrape_data_from_google_podcasts(query)

    assert result_dict["title"] == query
    assert expected_desc_snippet in result_dict["description"]
    assert result_dict["image_url"] == expected_img_url
    assert result_dict["producer"] == "NPR"
    assert result_dict["google_url"] == expected_google_url
