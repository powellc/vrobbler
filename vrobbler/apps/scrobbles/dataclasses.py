import inspect
import json
from dataclasses import asdict, dataclass
from typing import Optional

from dataclass_wizard import JSONWizard
from django.contrib.auth import get_user_model
from locations.models import GeoLocation

User = get_user_model()


class ScrobbleMetadataEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


class ScrobbleMetadataDecoder(json.JSONDecoder):
    def default(self, o):
        return o.__dict__


class JSONMetadata(JSONWizard):
    @property
    def asdict(self):
        return asdict(self)

    @property
    def json(self):
        return json.dumps(self.asdict)

    @classmethod
    def from_dict(cls, env):
        return cls(
            **{
                k: v
                for k, v in env.items()
                if k in inspect.signature(cls).parameters
            }
        )


@dataclass
class BoardGameScore(JSONMetadata):
    user_id: Optional[int] = None
    name: Optional[str] = None
    bgg_username: Optional[str] = None
    color: Optional[str] = None
    character: Optional[str] = None
    team: Optional[str] = None
    score: Optional[int] = None
    win: Optional[bool] = None


@dataclass
class BoardGameMetadata(JSONMetadata):
    players: Optional[list[BoardGameScore]] = None
    difficulty: Optional[int] = None
    solo: Optional[bool] = None
    two_handed: Optional[bool] = None
    location: Optional[str] = None

    def geo_location(self):
        return GeoLocation.objects.filter(id=self.geo_location_id).first()


@dataclass
class BookPageMetadata(JSONMetadata):
    page_number: Optional[int] = None
    end_ts: Optional[int] = None
    start_ts: Optional[int] = None
    duration: Optional[int] = None


@dataclass
class BookMetadata(JSONMetadata):
    koreader_hash: Optional[str]
    pages_read: Optional[int]
    page_data: Optional[list[BookPageMetadata]]


@dataclass
class LifeEventMetadata(JSONMetadata):
    participant_user_ids: Optional[list[int]] = None
    participant_names: Optional[list[str]] = None
    location: Optional[str] = None
    geo_location_id: Optional[int] = None
    details: Optional[str] = None

    def participants(self) -> list[str]:
        participants = []
        if self.participant_user_ids:
            participants += [u.full_name for u in self.participant_users]
        if self.participant_names:
            participants += self.participant_names
        return participants

    @property
    def participant_users(self) -> list[User]:
        participants = []
        if self.participant_user_ids:
            for id in self.participant_user_ids:
                participants.append(User.objects.filter(id=id).first())
        return participants

    def geo_location(self):
        return GeoLocation.objects.filter(id=self.geo_location_id).first()


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
