from vrobbler.apps.podcasts.scrapers import scrape_data_from_google_podcasts

expected_desc = (
    "NPR's Up First is the news you need to start your day. "
    "The three biggest stories of the day, with reporting and analysis "
    "from NPR News — in 10 minutes. Available weekdays by 6 a.m. ET, "
    "with hosts Leila Fadel, Steve Inskeep, Michel Martin and A Martinez. "
    "Also available on Saturdays by 8 a.m. ET, with Ayesha Rascoe and "
    "Scott Simon. On Sundays, hear a longer exploration behind the "
    "headlines with Rachel Martin, available by 8 a.m. ET. Subscribe "
    "and listen, then support your local NPR station at donate.npr.org.  "
    "Support NPR's reporting by subscribing to Up First+ and unlock "
    "sponsor-free listening. Learn more at plus.npr.org/UpFirst"
)

expected_img_url = "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcR1F0CfR24RR6sme531yIkCrnK4zzmo97jeualO5drVPKG6oCk"
expected_google_url = "https://podcasts.google.com/feed/aHR0cHM6Ly9mZWVkcy5ucHIub3JnLzUxMDMxOC9wb2RjYXN0LnhtbA"


def test_get_not_allowed_from_mopidy():
    query = "Up First"
    result_dict = scrape_data_from_google_podcasts(query)

    assert result_dict["title"] == query
    assert result_dict["description"] == expected_desc
    assert result_dict["image_url"] == expected_img_url
    assert result_dict["producer"] == "NPR"
    assert result_dict["google_url"] == expected_google_url
