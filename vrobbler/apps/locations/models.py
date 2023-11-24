import logging
from typing import Dict
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel
from scrobbles.mixins import ScrobblableMixin

logger = logging.getLogger(__name__)
BNULL = {"blank": True, "null": True}
User = get_user_model()


class GeoLocation(ScrobblableMixin):
    COMPLETION_PERCENT = getattr(settings, "LOCATION_COMPLETION_PERCENT", 100)

    uuid = models.UUIDField(default=uuid4, editable=False, **BNULL)
    lat = models.FloatField()
    lon = models.FloatField()
    altitude = models.FloatField(**BNULL)

    class Meta:
        unique_together = [["lat", "lon", "altitude"]]

    def __str__(self):
        return f"{self.lat} x {self.lon}"

    def get_absolute_url(self):
        return reverse(
            "locations:geo_location_detail", kwargs={"slug": self.uuid}
        )

    @property
    def truncated_lat(self):
        return float(str(self.lat)[:-3])

    @property
    def truncated_lan(self):
        return float(str(self.lon)[:-3])

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> "GeoLocation":
        """Given a data dict from GPSLogger, does the heavy lifting of looking up
        the location, creating if if doesn't exist yet.

        """
        # TODO Add constants for all these data keys
        if "lat" not in data_dict.keys() or "lon" not in data_dict.keys():
            logger.error("No lat or lon keys in data dict")
            return

        lat_int, lat_places = data_dict.get("lat", "").split(".")
        lon_int, lon_places = data_dict.get("lon", "").split(".")
        alt_int, alt_places = data_dict.get("alt", "").split(".")

        truncated_lat = lat_places[0:5]
        truncated_lon = lon_places[0:5]
        truncated_alt = alt_places[0:3]

        data_dict["lat"] = float(".".join([lat_int, truncated_lat]))
        data_dict["lon"] = float(".".join([lon_int, truncated_lon]))
        data_dict["altitude"] = float(".".join([alt_int, truncated_alt]))

        location = cls.objects.filter(
            lat=data_dict.get("lat"),
            lon=data_dict.get("lon"),
            altitude=data_dict.get("alt"),
        ).first()

        if not location:
            location = cls.objects.create(
                lat=data_dict.get("lat"),
                lon=data_dict.get("lon"),
                altitude=data_dict.get("alt"),
            )
        return location


class RawGeoLocation(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lat = models.FloatField()
    lon = models.FloatField()
    altitude = models.FloatField(**BNULL)
    speed = models.FloatField(**BNULL)
    timestamp = models.DateTimeField(**BNULL)
