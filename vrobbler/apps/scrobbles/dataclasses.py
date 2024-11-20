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


@dataclass
class ScrobbleLogData(JSONDataclass):
    description: Optional[str] = None


class LongPlayLogData(JSONDataclass):
    serial_scrobble_id: Optional[int]
    long_play_complete: bool = False


class WithOthersLogData(JSONDataclass):
    with_user_ids: Optional[list[int]] = None
    with_names_str: Optional[list[str]] = None

    @property
    def with_names(self) -> list[str]:
        with_names = []
        if self.with_user_ids:
            with_names += [u.full_name for u in self.with_users if u]
        if self.with_names_str:
            with_names += [u for u in self.with_names_str]
        return with_names

    @property
    def with_users(self) -> list[User]:
        with_users = []
        if self.with_user_ids:
            with_users = [
                User.objects.filter(id=i).first() for i in self.with_user_ids
            ]
        return with_users


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
    serial_scrobble_id: Optional[int] = None
    long_play_complete: Optional[bool] = None
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
    long_play_complete: Optional[bool] = None
    koreader_hash: Optional[str] = None
    page_data: Optional[dict[int, BookPageLogData]] = None
    pages_read: Optional[int] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    serial_scrobble_id: Optional[int] = None


@dataclass
class LifeEventLogData(WithOthersLogData):
    with_user_ids: Optional[list[int]] = None
    with_names_str: Optional[list[str]] = None
    location: Optional[str] = None
    geo_location_id: Optional[int] = None
    details: Optional[str] = None

    def geo_location(self):
        return GeoLocation.objects.filter(id=self.geo_location_id).first()


@dataclass
class MoodLogData(JSONDataclass):
    reasons: Optional[str] = None


@dataclass
class VideoLogData(JSONDataclass):
    title: str
    video_type: str
    run_time_seconds: int
    kind: str
    year: Optional[int]
    episode_number: Optional[int] = None
    source_url: Optional[str] = None
    imdbID: Optional[str] = None
    season_number: Optional[int] = None
    cover_url: Optional[str] = None
    next_imdb_id: Optional[int] = None
    tv_series_id: Optional[str] = None


@dataclass
class VideoGameLogData(LongPlayLogData):
    serial_scrobble_id: Optional[int] = None
    long_play_complete: Optional[bool] = False
    console: Optional[str] = None
    emulated: Optional[bool] = False
    emulator: Optional[str] = None


@dataclass
class BrickSetLogData(LongPlayLogData, WithOthersLogData):
    serial_scrobble_id: Optional[int]
    long_play_complete: bool = False
    with_user_ids: Optional[list[int]] = None
    with_names_str: Optional[list[str]] = None


@dataclass
class TrailLogData(WithOthersLogData):
    with_user_ids: Optional[list[int]] = None
    with_names_str: Optional[list[str]] = None
    details: Optional[str] = None
    effort: Optional[str] = None
    difficulty: Optional[str] = None


@dataclass
class BeerLogData(WithOthersLogData):
    with_user_ids: Optional[list[int]] = None
    with_names_str: Optional[list[str]] = None
    details: Optional[str] = None
    rating: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class FoodLogData(JSONDataclass):
    meal: Optional[str] = None
    details: Optional[str] = None
    rating: Optional[str] = None
    notes: Optional[str] = None
