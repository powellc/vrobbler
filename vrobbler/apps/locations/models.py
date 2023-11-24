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
    truncated_lat = models.FloatField(**BNULL)
    truncated_lon = models.FloatField(**BNULL)
    altitude = models.FloatField(**BNULL)

    class Meta:
        unique_together = [["lat", "lon", "altitude"]]

    def __str__(self):
        if self.title:
            return self.title

        return f"{self.lat} x {self.lon}"

    def get_absolute_url(self):
        return reverse(
            "locations:geo_location_detail", kwargs={"slug": self.uuid}
        )

    @classmethod
    def find_or_create(cls, data_dict: Dict) -> "GeoLocation":
        """Given a data dict from GPSLogger, does the heavy lifting of looking up
        the location, creating if if doesn't exist yet.

        """
        # TODO Add constants for all these data keys
        if "lat" not in data_dict.keys() or "lon" not in data_dict.keys():
            logger.error("No lat or lon keys in data dict")
            return

        int_lat, r_lat = str(data_dict.get("lat", "")).split(".")
        int_lon, r_lon = str(data_dict.get("lon", "")).split(".")

        try:
            trunc_lat = r_lat[0:4]
        except IndexError:
            trunc_lat = r_lat
        try:
            trunc_lon = r_lon[0:4]
        except IndexError:
            trunc_lon = r_lon

        data_dict["lat"] = float(f"{int_lat}.{trunc_lat}")
        data_dict["lon"] = float(f"{int_lon}.{trunc_lon}")

        int_alt, r_alt = str(data_dict.get("alt", "")).split(".")
        try:
            trunc_alt = r_lon[0:4]
        except IndexError:
            trunc_alt = r_alt

        data_dict["altitude"] = float(f"{int_alt}.{trunc_alt}")

        location = cls.objects.filter(
            lat=data_dict.get("lat"),
            lon=data_dict.get("lon"),
            altitude=data_dict.get("altitude"),
        ).first()

        if not location:
            location = cls.objects.create(
                lat=data_dict.get("lat"),
                lon=data_dict.get("lon"),
                altitude=data_dict.get("altitude"),
            )
        return location


class RawGeoLocation(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lat = models.FloatField()
    lon = models.FloatField()
    altitude = models.FloatField(**BNULL)
    speed = models.FloatField(**BNULL)
    timestamp = models.DateTimeField(**BNULL)
