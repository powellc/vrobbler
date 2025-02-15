Vrobbler
========

[![Build Status](https://ci.lab.unbl.ink/api/badges/secstate/vrobbler/status.svg?ref=refs/heads/main)](https://ci.lab.unbl.ink/secstate/vrobbler)

Vrobbler is a pretty simple Django-powered web app for scrobbling video plays from you favorite Jellyfin installation.

At the most basic level, you should be able to run `pip install vrobbler` to the latest version from pypi.org.

Then configure a handful of options in your vrobbler.conf files, which can live in /etc/ or /usr/local/etc/  depending on your configuration.

You can checkout the `scrobbler.conf.example` file in the source for this project, or refer to the following guide:

```
VROBBLER_DEBUG=True
VROBBLER_JSON_LOGGING=True
VROBBLER_LOG_LEVEL="DEBUG"
VROBBLER_MEDIA_ROOT = "/media/"
VROBBLER_TMDB_API_KEY = "<key>"
VROBBLER_KEEP_DETAILED_SCROBBLE_LOGS=True
VROBBLER_DATABASE_URL="postgres://vrobbler:<pass>@db.service:5432/vrobbler"
VROBBLER_REDIS_URL="redis://:<pass>@cache.service:6379/0"
```
