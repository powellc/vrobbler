from functools import cached_property
import inspect
import json
from dataclasses import asdict, dataclass
from typing import Optional

from dataclass_wizard import JSONWizard
from django.contrib.auth import get_user_model
from locations.models import GeoLocation

User = get_user_model()


class ScrobbleLogDataEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


class ScrobbleLogDataDecoder(json.JSONDecoder):
    def default(self, o):
        return o.__dict__


class JSONDataclass(JSONWizard):
    @property
    def asdict(self):
        return asdict(self)

    @property
    def json(self):
        return json.dumps(self.asdict)

class LongPlayLogData(JSONDataclass):
    serial_scrobble_id: Optional[int]
    long_play_complete: Optional[bool]

@dataclass
class BoardGameScoreLogData(JSONDataclass):
    user_id: Optional[int] = None
    name_str: str = ""
    bgg_username: str = ""
    color: Optional[str] = None
    character: Optional[str] = None
    team: Optional[str] = None
    score: Optional[int] = None
    win: Optional[bool] = None
    new: Optional[bool] = None

    @property
    def user(self) -> Optional[User]:
        user = None
        if self.user_id:
            user = User.objects.filter(id=self.user_id).first()
        return user

    @property
    def name(self) -> str:
        name = self.name_str
        if self.user_id:
            name = self.user.first_name
        return name

    def __str__(self) -> str:
        out = self.name
        if self.score:
            out += f" {self.score}"
        if self.color:
            out += f" ({self.color})"
        if self.win:
            out += f" [W]"
        return out


@dataclass
class BoardGameLogData(LongPlayLogData):
    players: Optional[list[BoardGameScoreLogData]] = None
    location: Optional[str] = None
    geo_location_id: Optional[int] = None
    difficulty: Optional[int] = None
    solo: Optional[bool] = None
    two_handed: Optional[bool] = None

    @cached_property
    def geo_location(self) -> Optional[GeoLocation]:
        if self.geo_location_id:
            return GeoLocation.objects.filter(id=self.geo_location_id).first()


@dataclass
class BookPageLogData(JSONDataclass):
    page_number: Optional[int] = None
    end_ts: Optional[int] = None
    start_ts: Optional[int] = None
    duration: Optional[int] = None


@dataclass
class BookLogData(LongPlayLogData):
    koreader_hash: Optional[str]
    pages_read: Optional[int]
    page_data: Optional[list[BookPageLogData]]
    page_end: Optional[int]
    page_start: Optional[int]
    serial_scrobble_id: Optional[int]


@dataclass
class LifeEventLogData(JSONDataclass):
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
class MoodLogData(JSONDataclass):
    reasons: Optional[str]


@dataclass
class VideoLogData(JSONDataclass):
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


@dataclass
class VideoGameLogData(LongPlayLogData):
    emulated: bool = False
    console: Optional[str] = None
    emulator: Optional[str] = None


@dataclass
class BrickSetLogData(LongPlayLogData):
    built_with_names: Optional[list[str]]
    built_with_user_ids: Optional[list[str]]
