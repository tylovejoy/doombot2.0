from __future__ import annotations
from datetime import datetime
from logging import getLogger
from typing import Generator, Optional, List, Literal

from beanie import Document
from pydantic import BaseModel

from utils.utilities import format_missions, tournament_category_map

CategoryLiteral = Literal["ta", "mc", "hc", "bo"]
DifficultyLiteral = Literal["easy", "medium", "hard", "expert"]

logger = getLogger(__name__)


class Announcement(Document):
    """Scheduled announcements."""

    embed: dict
    schedule: datetime
    mentions: str


class TournamentMaps(BaseModel):
    """Tournament data maps object."""

    code: str
    creator: str
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

    easy: TournamentMissions = TournamentMissions()
    medium: TournamentMissions = TournamentMissions()
    hard: TournamentMissions = TournamentMissions()
    expert: TournamentMissions = TournamentMissions()


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
    embed: Optional[dict]
    mentions: Optional[str]
    schedule_start: datetime
    schedule_end: datetime

    ta: Optional[TournamentData]
    mc: Optional[TournamentData]
    hc: Optional[TournamentData]
    bo: Optional[TournamentData]

    general: List[Optional[TournamentMissions]] = []

    @classmethod
    async def find_active(cls) -> Tournament:
        return await cls.find_one(cls.active == True)

    @classmethod
    async def find_latest(cls) -> Tournament:
        return (await cls.find().sort("-tournament_id").limit(1).to_list())[0]

    def get_categories(self) -> Generator[str]:
        for cat in ["ta", "mc", "hc", "bo"]:
            if getattr(self, cat, None):
                yield cat

    def get_map_str(self, category: CategoryLiteral) -> str:
        category = getattr(self, category, None)
        return f"{category.map_data.code} - {category.map_data.level} ({category.map_data.map_name}) by {category.map_data.creator}\n"

    def get_all_map_str(self) -> str:
        map_string = ""
        for category in self.get_categories():
            map_string += self.get_map_str(category)
        return map_string

    def get_map_str_short(self, category: str) -> str:
        category = getattr(self, category, None)
        return f"({category.map_data.code} - {category.map_data.level})"

    def get_records(self, category: CategoryLiteral) -> List[TournamentRecords]:
        category = getattr(self, category, None)
        return category.records

    def get_category_missions(self, category: CategoryLiteral) -> str:
        obj = getattr(self, category, None).missions
        missions = ""
        for difficulty in ["easy", "medium", "hard", "expert"]:
            curr = getattr(obj, difficulty, None)
            missions += f"- {difficulty.capitalize()}: " + format_missions(
                curr.type, curr.target
            )

        return missions

    def get_all_missions(self) -> str:
        missions = ""
        categories = list(self.get_categories())
        for category in categories:
            missions += f"**{tournament_category_map(category)} {self.get_map_str_short(category)}**\n"
            missions += self.get_category_missions(category)

        return missions

    def get_general(self) -> str:
        return f"{self.general.type} - {self.general.target}\n"
