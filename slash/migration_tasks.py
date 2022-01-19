import discord
from logging import getLogger

from database.documents import ExperiencePoints
from utils.constants import GUILD_ID
from utils.utilities import logging_util

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "EXP"))
    bot.application_command()


class MigrationTasks(discord.SlashCommand, guilds=[GUILD_ID], name="migrate"):
    """Migrate to doombot2.0"""

    async def callback(self) -> None:
        logger.info(logging_util("Migration", "BEGIN EXP TRANSFER"))
        members = self.interaction.guild.members
        member_list = []
        for member in members:
            member_list.append(
                ExperiencePoints(
                    user_id=member.id,
                    alias=member.name,
                    alerts_enabled=True,
                )
            )
            # TODO: add XP here ez
        await ExperiencePoints.insert_many(member_list)
