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
