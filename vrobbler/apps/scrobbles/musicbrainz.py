import logging

import musicbrainzngs
from dateutil.parser import parse

logger = logging.getLogger(__name__)


def lookup_album_from_mb(musicbrainz_id: str) -> dict:
    release_dict = {}

    musicbrainzngs.set_useragent('vrobbler', '0.3.0')
    release_data = musicbrainzngs.get_release_by_id(
        musicbrainz_id,
        includes=['artists', 'release-groups', 'recordings'],
    ).get('release')

    if not release_data:
        return release_dict

    primary_artist = release_data.get('artist-credit')[0]
    release_dict = {
        'artist': {
            'name': primary_artist.get('name'),
            'musicbrainz_id': primary_artist.get('id'),
        },
        'album': {
            'name': release_data.get('title'),
            'musicbrainz_id': musicbrainz_id,
            'musicbrainz_releasegroup_id': release_data.get(
                'release-group'
            ).get('id'),
            'musicbrainz_albumaritist_id': primary_artist.get('id'),
            'year': release_data.get('year')[0:4],
        },
    }

    release_dict['tracks'] = []
    for track in release_data.get('medium-list')[0]['track-list']:
        recording = track['recording']
        release_dict['tracks'].append(
            {
                'title': recording['title'],
                'musicbrainz_id': recording['id'],
                'run_time_ticks': track['length'],
            }
        )

    return release_dict


def lookup_album_dict_from_mb(release_name: str, artist_name: str) -> dict:
    musicbrainzngs.set_useragent('vrobbler', '0.3.0')

    top_result = musicbrainzngs.search_releases(
        release_name, artist=artist_name
    )['release-list'][0]
    score = int(top_result.get('ext:score'))
    if score < 85:
        logger.debug(
            "Album lookup score below 85 threshold",
            extra={"result": top_result},
        )
        return {}
    year = None
    if top_result.get("date"):
        year = parse(top_result["date"]).year

    return {
        "year": year,
        "mb_id": top_result["id"],
        "mb_group_id": top_result["release-group"]["id"],
    }


def lookup_artist_from_mb(artist_name: str) -> str:
    musicbrainzngs.set_useragent('vrobbler', '0.3.0')

    top_result = musicbrainzngs.search_artists(artist=artist_name)[
        'artist-list'
    ][0]
    score = int(top_result.get('ext:score'))
    if score < 85:
        logger.debug(
            "Artist lookup score below 85 threshold",
            extra={"result": top_result},
        )
        return ""

    return top_result


def lookup_track_from_mb(
    track_name: str, artist_mbid: str, album_mbid: str
) -> str:
    musicbrainzngs.set_useragent('vrobbler', '0.3.0')

    top_result = musicbrainzngs.search_recordings(
        query=track_name, artist=artist_mbid, release=album_mbid
    )['recording-list'][0]
    score = int(top_result.get('ext:score'))
    if score < 85:
        logger.debug(
            "Track lookup score below 85 threshold",
            extra={"result": top_result},
        )
        return ""

    return top_result
