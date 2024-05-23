import json
from dataclasses import dataclass, asdict

from typing import Optional


class ScrobbleMetadataEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


class ScrobbleMetadataDecoder(json.JSONDecoder):
    def default(self, o):
        return o.__dict__


class JSONMetadata(object):
    @property
    def asdict(self):
        return asdict(self)

    @property
    def json(self):
        return json.dumps(self.asdict)


@dataclass
class BoardGameScore(JSONMetadata):
    user_id: int
    score: Optional[int]
    win: Optional[bool]


@dataclass
class BoardGameMetadata(JSONMetadata):
    players: Optional[list[BoardGameScore]]


@dataclass
class LifeEventMetadata(JSONMetadata):
    location: Optional[str]
    geo_location_id: Optional[int]
    participant_user_ids: Optional[list[int]]

    @property
    def __dict__(self):
        return asdict(self)

    @property
    def json(self):
        return json.dumps(self.__dict__)


@dataclass
class VideoMetadata(JSONMetadata):
    title: str
    video_type: str
    run_time_seconds: int
    kind: str
    year: Optional[int]
    episode_number: Optional[int]
    source_url: Optional[str]
    imdbID: Optional[str]
    season_number: Optional[int]
    cover_url = Optional[str]
    next_imdb_id: Optional[int]
    tv_series_id: Optional[str]
