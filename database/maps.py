from __future__ import annotations

from typing import Any, List, NoReturn, Optional

from beanie import Document
from beanie.odm.fields import Indexed
from beanie.odm.operators.find.evaluation import RegEx
from pydantic import BaseModel, Field

from utils.errors import MapCodeDoesNotExist


class MapAlias(Document):
    """Aliases for Map codes."""

    alias: str
    original_code: str

    @classmethod
    async def get_alias(cls, map_code: str) -> str:

        return getattr(await cls.find_one(cls.alias == map_code), "original_code", None)


class MapLevels(BaseModel):
    """Projection model for Map aggregation."""

    _id: Optional[None]
    level: str

    def __str__(self) -> str:
        """String representation."""
        return self.level


class MapCodes(BaseModel):
    """Project model for Map aggregation."""

    code: str
    map_data: list

    def __str__(self) -> str:
        """String representation."""
        return self.code

    def get_data(self) -> str:
        """Get the code and creator/map name if submitted to the database."""
        if self.map_data:
            return f"{self.code} -- ({self.map_data[0]['map_name']} by {self.map_data[0]['creator']})"
        return self.code


class Map(Document):
    """Collection of Maps."""

    user_id: int
    code: Indexed(str, unique=True)
    creator: str
    map_name: str
    map_type: Optional[List[str]]
    description: Optional[str]

    @classmethod
    async def find_one_map(cls, map_code: str) -> Map:
        """Find a single map using its workshop code."""
        return await cls.find_one(cls.code == map_code)

    @classmethod
    async def check_code(cls, map_code: str) -> NoReturn:
        """Check if a map exists with specific map_code."""
        if not await cls.find_one(cls.code == map_code).exists():
            raise MapCodeDoesNotExist(
                "This workshop code doesn't exist in the database!"
            )

    @classmethod
    async def get_all_maps(cls, map_name: str) -> List[Map]:
        """Get all maps with a particular map name."""
        return await cls.find(cls.map_name == map_name).to_list()

    @classmethod
    async def filter_search(cls, **filters: Any) -> List[Map]:
        """Get all amps with a particular filter."""
        map_name = filters.get("map_name")
        map_type = filters.get("map_type")
        creator = filters.get("creator")

        search_filter = {}

        if map_name:
            search_filter.update({"map_name": map_name})
        if map_type:
            search_filter.update({"map_type": map_type})
        if creator:
            creators = [x.strip() for x in creator.split(",")]
            if len(creators) == 1:
                search_filter.update(RegEx("creator", creator, "i"))
            else:
                search_filter.update(
                    {"$and": [RegEx("creator", x, "i") for x in creators]}
                )

        return await cls.find(search_filter).to_list()

    @classmethod
    async def random(cls, amount: int) -> List[Map]:
        """Find {amount} random maps."""
        return (
            await cls.find()
            .aggregate([{"$sample": {"size": amount}}], projection_model=cls)
            .to_list()
        )
