import json
import logging

import requests
from django.conf import settings

THEAUDIODB_API_KEY = getattr(settings, "THEAUDIODB_API_KEY")
ARTIST_SEARCH_URL = f"https://www.theaudiodb.com/api/v1/json/{THEAUDIODB_API_KEY}/search.php?s="
ALBUM_SEARCH_URL = f"https://www.theaudiodb.com/api/v1/json/{THEAUDIODB_API_KEY}/searchalbum.php?s="

logger = logging.getLogger(__name__)


def lookup_artist_from_tadb(name: str) -> dict:
    artist_info = {}
    response = requests.get(ARTIST_SEARCH_URL + name)

    if response.status_code != 200:
        logger.warn(f"Bad response from TADB: {response.status_code}")
        return {}

    if not response.content:
        logger.warn(f"Bad content from TADB: {response.content}")
        return {}

    results = json.loads(response.content)
    if results['artists']:
        artist = results['artists'][0]

        artist_info['biography'] = artist.get('strBiographyEN')
        artist_info['genre'] = artist.get('strGenre')
        artist_info['mood'] = artist.get('strMood')
        artist_info['thumb_url'] = artist.get('strArtistThumb')

    return artist_info


def lookup_album_from_tadb(name: str, artist: str) -> dict:
    album_info = {}
    response = requests.get(''.join([ALBUM_SEARCH_URL, artist, "&a=", name]))

    if response.status_code != 200:
        logger.warn(f"Bad response from TADB: {response.status_code}")
        return {}

    if not response.content:
        logger.warn(f"Bad content from TADB: {response.content}")
        return {}

    results = json.loads(response.content)
    if results['album']:
        album = results['album'][0]

        album_info['theaudiodb_id'] = album.get('idAlbum')
        album_info['theaudiodb_description'] = album.get('strDescriptionEN')
        album_info['theaudiodb_genre'] = album.get('strGenre')
        album_info['theaudiodb_style'] = album.get('strStyle')
        album_info['theaudiodb_mood'] = album.get('strMood')
        album_info['theaudiodb_speed'] = album.get('strSpeed')
        album_info['theaudiodb_theme'] = album.get('strTheme')
        album_info['allmusic_id'] = album.get('strAllMusicID')
        album_info['wikipedia_slug'] = album.get('strWikipediaID')
        album_info['discogs_id'] = album.get('strDiscogsID')
        album_info['wikidata_id'] = album.get('strWikidataID')
        album_info['rateyourmusic_id'] = album.get('strRateYourMusicID')

        if album.get('intYearReleased'):
            album_info['theaudiodb_year_released'] = float(
                album.get('intYearReleased')
            )
        if album.get('intScore'):
            album_info['theaudiodb_score'] = float(album.get('intScore'))
        if album.get('intScoreVotes'):
            album_info['theaudiodb_score_votes'] = int(
                album.get('intScoreVotes')
            )

    return album_info
