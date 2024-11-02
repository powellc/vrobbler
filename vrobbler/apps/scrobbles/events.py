from dataclasses import dataclass


class Event:
    pass


@dataclass
class Start(Event):
    scrobble_id: str


@dataclass
class Pause(Event):
    scrobble_id: str


@dataclass
class Cancel(Event):
    scrobble_id: str


@dataclass
class Stop(Event):
    scrobble_id: str
