from decimal import Decimal
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

GEOLOC_ACCURACY = int(getattr(settings, "GEOLOC_ACCURACY", 4))
GEOLOC_PROXIMITY = Decimal(getattr(settings, "GEOLOC_PROXIMITY", "0.0001"))


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
            trunc_lat = r_lat[0:GEOLOC_ACCURACY]
        except IndexError:
            trunc_lat = r_lat
        try:
            trunc_lon = r_lon[0:GEOLOC_ACCURACY]
        except IndexError:
            trunc_lon = r_lon

        data_dict["lat"] = float(f"{int_lat}.{trunc_lat}")
        data_dict["lon"] = float(f"{int_lon}.{trunc_lon}")

        int_alt, r_alt = str(data_dict.get("alt", "")).split(".")

        data_dict["altitude"] = float(int_alt)

        location = cls.objects.filter(
            lat=data_dict.get("lat"),
            lon=data_dict.get("lon"),
        ).first()

        if not location:
            location = cls.objects.create(
                lat=data_dict.get("lat"),
                lon=data_dict.get("lon"),
                altitude=data_dict.get("altitude"),
            )
        return location

    def loc_diff(self, old_lat_lon: tuple) -> tuple:
        return (
            abs(Decimal(old_lat_lon[0]) - Decimal(self.lat)),
            abs(Decimal(old_lat_lon[1]) - Decimal(self.lon)),
        )

    def has_moved(self, past_points: list["GeoLocation"]) -> bool:
        """GPS jumps from time to time. This function tries to smooth out
        when we appear to have flagging our location as having not moved if one of our last
        3"""
        has_moved = False
        has_moved_locs = []
        for point in past_points:
            loc_diff = self.loc_diff((point.lat, point.lon))
            logger.info(
                f"[locations] checking whether location has moved",
                extra={"location": self, "loc_diff": loc_diff, "point": point},
            )
            if (
                loc_diff[0] > GEOLOC_PROXIMITY
                or loc_diff[1] > GEOLOC_PROXIMITY
            ):
                logger.info(
                    f"[locations] difference is less than proximity setting, we may have moved",
                    extra={
                        "loc_diff": loc_diff,
                        "point": point,
                        "geoloc_proximity": GEOLOC_PROXIMITY,
                    },
                )
                has_moved_locs.append(True)
            else:
                has_moved_locs.append(False)

        # Sum up all True values, if they're more than half of our locations, we've moved
        if sum(has_moved_locs) > int(len(past_points) / 2):
            logger.info(
                f"[locations] more than half of past points have moved, we've moved",
                extra={
                    "has_moved_locs": has_moved_locs,
                    "past_points": past_points,
                },
            )
            has_moved = True

        return has_moved

    def in_proximity(self, named=True) -> models.QuerySet:
        lat_min = Decimal(self.lat) - GEOLOC_PROXIMITY
        lat_max = Decimal(self.lat) + GEOLOC_PROXIMITY
        lon_min = Decimal(self.lon) - GEOLOC_PROXIMITY
        lon_max = Decimal(self.lon) + GEOLOC_PROXIMITY
        is_title_null = not named
        return GeoLocation.objects.filter(
            title__isnull=is_title_null,
            lat__lte=lat_max,
            lat__gte=lat_min,
            lon__lte=lon_max,
            lon__gte=lon_min,
        )
