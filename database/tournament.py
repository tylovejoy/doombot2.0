from datetime import datetime
from logging import getLogger
from time import mktime
from typing import Optional, Union, List, Literal

from beanie import Document
from pydantic import BaseModel

CategoryLiteral = Literal["ta", "mc", "hc", "bo"]
DifficultyLiteral = Literal["easy", "medium", "hard", "expert"]

logger = getLogger(__name__)


class TournamentMaps(BaseModel):

    """Tournament data maps object."""

    code: str
    creator: str
    map_name: str
    level: str


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

    easy: Optional[TournamentMissions] = TournamentMissions()
    medium: Optional[TournamentMissions] = TournamentMissions()
    hard: Optional[TournamentMissions] = TournamentMissions()
    expert: Optional[TournamentMissions] = TournamentMissions()


class TournamentData(BaseModel):

    """Base models for tournament categories."""

    map_data: TournamentMaps
    records: List[Optional[TournamentRecords]] = []
    missions: TournamentMissionsCategories = TournamentMissionsCategories()


class Tournament(Document):

    """Collection of Tournament data."""

    tournament_id: int
    name: str
    active: bool
    bracket: bool
    bracket_category: Optional[str]
    schedule_start: datetime
    schedule_end: datetime

    ta: Optional[TournamentData]
    mc: Optional[TournamentData]
    hc: Optional[TournamentData]
    bo: Optional[TournamentData]

    @staticmethod
    def get_unix_timestamp(dt: datetime) -> int:
        return int(mktime(dt.timetuple()))

    @classmethod
    async def find_latest(cls):
        return (await cls.find().sort("-tournament_id").limit(1).to_list())[0]

    def get_map_str(self, category: CategoryLiteral) -> str:
        category = getattr(self, category)
        return f"{category.map_data.code} - {category.map_data.level} ({category.map_data.map_name}) by {category.map_data.creator}\n"

    def get_all_map_str(self) -> str:
        map_string = ""
        for category in ["ta", "mc", "hc", "bo"]:
            map_string += self.get_map_str(category)
        return map_string

    def get_records(self, category: CategoryLiteral) -> List[TournamentRecords]:
        category = getattr(self, category)
        return category.records

    def get_difficulty_missions(self, difficulty: DifficultyLiteral):
        missions = ""
        for cat in ["ta", "mc", "hc", "bo"]:
            category = getattr(getattr(self, cat).missions, difficulty)
            missions += f"{category.type} - {category.target}\n"
        return missions

    def get_category_missions(self, category: CategoryLiteral):
        category = getattr(self, category)
        missions = ""
        for difficulty in ["easy", "medium", "hard", "expert"]:
            diff = getattr(category.missions, difficulty)
            missions += f"{diff.type} - {diff.target}\n"
        return missions

    def get_all_missions(self):
        missions = ""
        map_ = {"ta": "Time Attack", "mc": "Mildcore", "hc": "Hardcore", "bo": "Bonus"}
        for category in map_.keys():
            missions += f"**{map_[category]}:**\n"
            missions += self.get_category_missions(category)
        return missions

    def get_unix_start(self):
        return self.get_unix_timestamp(self.schedule_start)

    def get_unix_end(self):
        return self.get_unix_timestamp(self.schedule_end)
