import inspect
import json
from dataclasses import asdict, dataclass
from typing import Optional

from dataclass_wizard import JSONWizard
from django.contrib.auth import get_user_model

from vrobbler.apps.locations.models import GeoLocation

User = get_user_model()


class ScrobbleMetadataEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


class ScrobbleMetadataDecoder(json.JSONDecoder):
    def default(self, o):
        return o.__dict__


class BaseJSONMetadata(JSONWizard):
    @property
    def asdict(self):
        return asdict(self)

    @property
    def json(self):
        return json.dumps(self.asdict)


@dataclass
class BoardGameScore(BaseJSONMetadata):
    user_id: Optional[int] = None
    name: Optional[str] = None
    color: Optional[str] = None
    score: Optional[int] = None
    win: Optional[bool] = None
    location: Optional[str] = None
    geo_location_id: Optional[int] = None

    def user(self):
        return User.objects.filter(id=self.user_id).first()


@dataclass
class BoardGameMetadata(BaseJSONMetadata):
    players: Optional[list[BoardGameScore]] = None

    def geo_location(self):
        return GeoLocation.objects.filter(id=self.geo_location_id).first()


@dataclass
class LifeEventMetadata(BaseJSONMetadata):
    participant_user_ids: Optional[list[int]] = None
    location: Optional[str] = None
    geo_location_id: Optional[int] = None

    @property
    def __dict__(self):
        return asdict(self)

    @property
    def json(self):
        return json.dumps(self.__dict__)

    def participants(self) -> list[User]:
        participants = []
        if self.participant_user_ids:
            for id in self.participant_user_ids:
                participants.append(User.objects.filter(id=id).first())
        return participants

    def geo_location(self):
        return GeoLocation.objects.filter(id=self.geo_location_id).first()


@dataclass
class VideoMetadata(BaseJSONMetadata):
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
