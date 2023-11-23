#!/usr/bin/env python3
from collections import defaultdict


LOCATION_PROVIDERS = defaultdict(lambda: "Unknown")
LOCATION_PROVIDERS["gps"] = "GPS"
LOCATION_PROVIDERS["network"] = "Wifi Triangulation"
