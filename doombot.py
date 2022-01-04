from logging import getLogger

import discord
from discord.ext import commands

from database.documents import database_init
from utils.constants import BOT_ID, SUGGESTIONS_ID, TOP_SUGGESTIONS_ID
from utils.utilities import star_emoji

logger = getLogger(__name__)

DOOMBOT_ASCII = r"""
______  _____  _____ ___  _________  _____  _____
|  _  \|  _  ||  _  ||  \/  || ___ \|  _  ||_   _|
| | | || | | || | | || .  . || |_/ /| | | |  | |
| | | || | | || | | || |\/| || ___ \| | | |  | |
| |/ / \ \_/ /\ \_/ /| |  | || |_/ /\ \_/ /  | |
|___/   \___/  \___/ \_|  |_/\____/  \___/   \_/
"""


class DoomBot(discord.Client):
    def __init__(self, **kwargs):
        """Initialize Bot."""
        intents = discord.Intents(
            guild_reactions=True,
            guild_messages=True,
            guilds=True,
            dm_reactions=True,
            dm_messages=True,
            webhooks=True,
            members=True,
            emojis=True,
        )
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"),
            case_insensitive=True,
            description="",
            intents=intents,
            slash_command_guilds=[195387617972322306],
        )
        self.suggestion_channel = self.get_channel(SUGGESTIONS_ID)
        self.starboard_channel = self.get_channel(TOP_SUGGESTIONS_ID)

    async def on_ready(self):
        """Display bot info on ready event."""
        app_info = await self.application_info()
        logger.info(
            f"{DOOMBOT_ASCII}"
            f"\nLogged in as: {self.user.name}\n"
            f"Using discord.py version: {discord.__version__}\n"
            f"Owner: {app_info.owner}\n"
        )
        await database_init()

    async def on_message(self, message: discord.Message):
        await self.process_commands(message)

        # Suggestions
        if message.channel.id == SUGGESTIONS_ID:
            await message.add_reaction(emoji="<:upper:787788134620332063>")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == BOT_ID:
            return
        if payload.channel_id != SUGGESTIONS_ID:
            return
        if payload.emoji != discord.PartialEmoji.from_str(
            "<:upper:787788134620332063>"
        ):
            return

        entry: SuggestionStars = await SuggestionStars.search(payload.message_id)
        if entry is None:
            entry = SuggestionStars(
                **{
                    "message_id": payload.message_id,
                    "stars": 0,
                    "jump": f"https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}",
                    "starboard_id": 0,
                    "reacted": [],
                }
            )
        elif payload.user_id in entry.reacted:
            return

        entry.stars += 1
        entry.reacted = entry.reacted + [payload.user_id]
        await entry.commit()
        if entry.stars < 10:
            return

        message: discord.Message = await self.suggestion_channel.get_partial_message(
            payload.message_id
        ).fetch()

        if entry.starboard_id == 0:
            embed = discord.Embed(
                description=message.content,
                color=0xF7BD00,
            )
            embed.set_author(
                name=message.author.name, icon_url=message.author.avatar.url
            )
            embed.add_field(name="Original", value=f"[Jump!]({entry.jump})")
            starboard_message: discord.Message = await self.starboard_channel.send(
                f"{star_emoji(entry.stars)} **{entry.stars}**",
                embed=embed,
            )
            entry.starboard_id = starboard_message.id
            await entry.commit()
            thread = await starboard_message.start_thread(
                name=message.content[:100], auto_archive_duration=1440
            )
            await thread.add_user(message.author)

        else:
            starboard_message = self.starboard_channel.get_partial_message(
                entry.starboard_id
            )
            await starboard_message.edit(
                content=f"{star_emoji(entry.stars)} **{entry.stars}**"
            )
