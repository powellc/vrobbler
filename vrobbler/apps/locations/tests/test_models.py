import pytest
import logging

from locations.models import GeoLocation

logger = logging.getLogger(__name__)


def test_find_or_create(caplog):
    assert not GeoLocation.find_or_create({})
    assert "No lat or lon keys in data dict" in caplog.text


@pytest.mark.django_db
def test_find_or_create_truncation():
    loc = GeoLocation.find_or_create(
        {"lat": 44.2345, "lon": -68.2345, "alt": 60.356}
    )
    assert loc.lat == 44.234
    assert loc.lon == -68.234
    assert loc.altitude == 60


@pytest.mark.django_db
def test_find_or_create_finds_existing():
    extant = GeoLocation.objects.create(lat=44.234, lon=-68.234, altitude=50)

    loc = GeoLocation.find_or_create(
        {"lat": 44.2345, "lon": -68.2345, "alt": 60.356}
    )
    assert loc.id == extant.id


@pytest.mark.django_db
def test_find_or_create_creates_new():
    extant = GeoLocation.objects.create(lat=44.234, lon=-69.234, altitude=60)

    loc = GeoLocation.find_or_create(
        {"lat": 44.2345, "lon": -68.2345, "alt": 60.356}
    )
    assert not loc.id == extant.id


@pytest.mark.django_db
def test_found_in_proximity_location():
    lat = 44.234
    lon = -69.234
    loc = GeoLocation.objects.create(lat=lat, lon=lon, altitude=60)

    close = GeoLocation.objects.create(
        lat=lat + 0.0001, lon=lon - 0.0001, altitude=60
    )
    assert close not in loc.in_proximity(named=True)
    assert close in loc.in_proximity()


@pytest.mark.django_db
def test_not_found_in_proximity_location():
    lat = 44.234
    lon = -69.234
    loc = GeoLocation.objects.create(lat=lat, lon=lon, altitude=60)

    far = GeoLocation.objects.create(
        lat=lat + 0.0002, lon=lon - 0.0001, altitude=60
    )
    assert far not in loc.in_proximity()


@pytest.mark.django_db
def test_has_moved(caplog):
    lat = 44.234
    lon = -69.234
    loc = GeoLocation.objects.create(lat=lat, lon=lon, altitude=60)

    past1 = GeoLocation.objects.get_or_create(
        lat=lat + 0.000, lon=lon - 0.000, altitude=60
    )[0]
    past2 = GeoLocation.objects.get_or_create(
        lat=lat + 0.002, lon=lon - 0.002, altitude=60
    )[0]
    past3 = GeoLocation.objects.get_or_create(
        lat=lat + 0.0001, lon=lon - 0.000, altitude=60
    )[0]
    last_three = [past1, past2, past3]
    assert loc.has_moved(last_three)


@pytest.mark.django_db
def test_has_not_moved():
    lat = 44.234
    lon = -69.234
    loc = GeoLocation.objects.create(lat=lat, lon=lon, altitude=60)

    past1 = GeoLocation.objects.get_or_create(
        lat=lat + 0.00001, lon=lon - 0.0000, altitude=60
    )[0]
    past2 = GeoLocation.objects.get_or_create(
        lat=lat + 0.000, lon=lon - 0.000, altitude=60
    )[0]
    past3 = GeoLocation.objects.get_or_create(
        lat=lat + 0.0000, lon=lon - 0.00001, altitude=60
    )[0]
    past4 = GeoLocation.objects.get_or_create(
        lat=lat + 0.005, lon=lon - 0.0003, altitude=60
    )[0]
    last_four = [past1, past2, past3, past4]
    assert not loc.has_moved(last_four)
