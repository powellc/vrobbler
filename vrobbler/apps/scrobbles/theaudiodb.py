import json
import logging

import requests
from django.conf import settings

THEAUDIODB_API_KEY = getattr(settings, "THEAUDIODB_API_KEY")
SEARCH_URL = f"https://www.theaudiodb.com/api/v1/json/{THEAUDIODB_API_KEY}/search.php?s="

logger = logging.getLogger(__name__)


def lookup_artist_from_tadb(name: str) -> dict:
    artist_info = {}
    response = requests.get(SEARCH_URL + name)

    if response.status_code != 200:
        logger.warn(f"Bad response from TADB: {response.status_code}")
        return {}

    if not response.content:
        logger.warn(f"Bad content from TADB: {response.content}")
        return {}

    results = json.loads(response.content)
    if results['artists']:
        artist = results['artists'][0]

        artist_info['biography'] = artist['strBiographyEN']
        artist_info['genre'] = artist['strGenre']
        artist_info['mood'] = artist['strMood']
        artist_info['thumb_url'] = artist['strArtistThumb']

    return artist_info
