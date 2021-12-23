from __future__ import annotations
from datetime import datetime
from logging import getLogger
from typing import Generator, Optional, List, Literal, Tuple

from beanie import Document
from pydantic import BaseModel

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
    embed: Optional[dict]
    mentions: str
    schedule_start: datetime
    schedule_end: datetime

    ta: Optional[TournamentData]
    mc: Optional[TournamentData]
    hc: Optional[TournamentData]
    bo: Optional[TournamentData]

    general_mission: TournamentMissions = TournamentMissions()

    @classmethod
    async def find_latest(cls) -> Tournament:
        return (await cls.find().sort("-tournament_id").limit(1).to_list())[0]

    def is_active(self) -> bool:
        if self.schedule_end > datetime.now():
            return True

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

    def get_records(self, category: CategoryLiteral) -> List[TournamentRecords]:
        category = getattr(self, category, None)
        return category.records

    def get_difficulty_missions(self, difficulty: DifficultyLiteral) -> str:
        missions = ""
        for cat in self.get_categories():
            category = getattr(getattr(self, cat, None).missions, difficulty, None)
            missions += f"{category.type} - {category.target}\n"
        return missions

    def get_category_missions(self, category: CategoryLiteral) -> str:
        obj = getattr(self, category, None)
        missions = ""
        for difficulty in ["easy", "medium", "hard", "expert"]:
            curr = getattr(obj.missions, difficulty, None)
            missions += format_missions(curr, difficulty)

        return missions

    def get_all_missions(self) -> str:
        missions = ""
        map_ = {"ta": "Time Attack", "mc": "Mildcore", "hc": "Hardcore", "bo": "Bonus"}
        for category in map_.keys():
            if category in self.get_categories():
                missions += f"**{map_[category]}:**\n"
                missions += self.get_category_missions(category)
        return missions

    def get_general_mission(self) -> str:
        return f"{self.general_mission.type} - {self.general_mission.target}\n"


def format_missions(
    mission: TournamentMissions, difficulty: DifficultyLiteral, is_general: bool = False
) -> str:
    """Format missions into user friendly strings."""
    formatted = ""

    if is_general:
        if mission.type == "xp":
            formatted += f"Get {mission.target} XP (excluding missions)\n"
        elif mission.type == "mission":
            formatted += f"Complete {mission.target[0]} {mission.target[1]} missions\n"
        elif mission.type == "top":
            formatted += f"Get Top 3 in {mission.target} categories.\n"
    else:
        if mission.type == "sub":
            formatted += f"**{difficulty.capitalize()}:** Get {mission.type} {mission.target} seconds.\n"
        elif mission.type == "complete":
            formatted += f"**{difficulty.capitalize()}:** Complete the level.\n"

    return formatted
