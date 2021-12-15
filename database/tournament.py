from datetime import datetime
from logging import getLogger
from time import mktime
from typing import Optional, Union, List, Literal

from beanie import Document
from pydantic import BaseModel

CategoryLiteral = Literal["ta", "mc", "hc", "bo"]

logger = getLogger(__name__)


class TournamentMaps(BaseModel):

    """Tournament data maps object."""

    code: str
    creator: str
    map_name: str


class TournamentRecords(BaseModel):
    """Base model for tournament records."""

    record: float
    posted_by: int
    attachment_url: str


class TournamentMissions(BaseModel):
    """Base model for tournament missions."""

    type: Optional[str]
    target: Optional[str]


class TournamentMissionsCategories(BaseModel):
    """Base model for tournament mission categories."""

    easy: Optional[TournamentMissions]
    medium: Optional[TournamentMissions]
    hard: Optional[TournamentMissions]
    expert: Optional[TournamentMissions]


class TournamentCategories(BaseModel):

    """Base models for tournament categories."""

    ta: Union[
        TournamentMaps,
        Optional[List[TournamentRecords]],
        Optional[TournamentMissionsCategories],
    ]
    mc: Union[
        TournamentMaps,
        Optional[List[TournamentRecords]],
        Optional[TournamentMissionsCategories],
    ]
    hc: Union[
        TournamentMaps,
        Optional[List[TournamentRecords]],
        Optional[TournamentMissionsCategories],
    ]
    bo: Union[
        TournamentMaps,
        Optional[List[TournamentRecords]],
        Optional[TournamentMissionsCategories],
    ]


class Tournament(Document):

    """Collection of Tournament data."""

    tournament_id: int
    name: str
    active: bool
    bracket: bool
    bracket_category: Optional[str]
    schedule_start: datetime
    schedule_end: datetime

    maps: TournamentCategories
    records: TournamentCategories
    missions: TournamentCategories

    @staticmethod
    def get_unix_timestamp(dt: datetime) -> str:
        return str(mktime(dt.timetuple()))

    @classmethod
    async def find_latest(cls):
        return (await cls.find().sort("-tournament_id").limit(1).to_list())[0]

    def get_map_str(self, category: CategoryLiteral) -> str:
        return f"{self.maps[category]['code']} - {self.maps[category]['level']} by {self.maps[category]['author']}\n"

    def get_all_map_str(self) -> str:
        return (
            self.get_map_str("ta")
            + self.get_map_str("mc")
            + self.get_map_str("hc")
            + self.get_map_str("bo")
        )

    def get_records(self, category: CategoryLiteral) -> List[TournamentRecords]:
        return self.records[category]

    def get_unix_start(self):
        return self.get_unix_timestamp(self.schedule_start)

    def get_unix_end(self):
        return self.get_unix_timestamp(self.schedule_end)
