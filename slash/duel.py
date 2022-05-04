from logging import getLogger

import datetime
import discord
from database.documents import ExperiencePoints

from slash.records import check_user
from utils.constants import DUELS_ID, GUILD_ID
from slash.slash_command import RecordSlash, Slash
from utils.embed import create_embed
from views.basic import ConfirmView
from views.records import RecordSubmitView
from views.tournament import DuelReadyView
from utils.utilities import (
    display_record,
    logging_util,
    preprocess_map_code,
    preprocess_level_name,
    time_convert,
)
from database.tournament import Duel, DuelPlayer
from utils.errors import TournamentStateError, RecordNotFaster

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "DUELS"))
    bot.application_command(DuelParent)


class DuelParent(Slash, guilds=[GUILD_ID], name="duel"):
    """Duel parent."""


class DuelStart(
    RecordSlash,
    guilds=[GUILD_ID],
    name="start",
    parent=DuelParent,
):
    """Start a duel with another player."""

    user: discord.Member = discord.Option(description="Which user do you want to duel?")
    wager: int = discord.Option(
        description="How much XP would you like to wager?",
        min=0,
    )
    map_code: str = discord.Option(description="Which map code?", autocomplete=True)
    map_level: str = discord.Option(description="Which level?", autocomplete=True)

    async def callback(self) -> None:
        await self.defer(ephemeral=True)

        if await Duel.find_duel(self.interaction.user.id):
            raise TournamentStateError("You are already in a duel.")

        if self.interaction.user.id == self.user.id:
            raise TournamentStateError("You cannot duel yourself.")

        self.map_code = preprocess_map_code(self.map_code)
        self.map_level = preprocess_level_name(self.map_level)

        xp = (await check_user(self.interaction.user)).xp 
        xp_opponent = (await check_user(self.user)).xp
        if xp is None:
            xp = 0
        if xp_opponent is None:
            xp_opponent = 0

        if self.wager > xp or self.wager > xp_opponent:
            raise TournamentStateError("You can't wager more XP than either player has.")


        view = ConfirmView()

        start_msg = (
            f"***{self.interaction.user.name}*** VS. ***{self.user.name}***\n\n"
            f"**Wager:** {self.wager}\n"
            f"**Code:** {self.map_code}\n"
            f"**Level:** {self.map_level}\n"
        )
        if not await view.start(
            self.interaction,
            "Is this correct?\n" + start_msg,
            f"Starting duel...",
        ):
            return

        channel = self.interaction.guild.get_channel(DUELS_ID)
        message = await channel.send(start_msg)
        thread = await channel.create_thread(
            name=f"{self.interaction.user.name} VS. {self.user.name}",
            message=message,
        )
        standby = discord.utils.utcnow() + datetime.timedelta(hours=12)

        await thread.add_user(self.user)
        await thread.add_user(self.interaction.user)

        view = DuelReadyView(self.interaction)
        thread_msg = await thread.send(
            f"{self.interaction.user.mention} has challenged you!\n"
            f"{self.user.mention} You need to **READY UP!**\n\n"
            "Time left to ready up:\n"
            f"{discord.utils.format_dt(standby)} | {discord.utils.format_dt(standby, style='R')}",
            view=view,
        )
        view.message = thread_msg
        duel = Duel(
            player1=DuelPlayer(
                user_id=self.interaction.user.id,
                ready=True,
            ),
            player2=DuelPlayer(
                user_id=self.user.id,
                ready=False,
            ),
            thread=thread.id,
            standby_time=standby,
            message=thread_msg.id,
            wager=self.wager,
        )
        await duel.save()


class DuelSubmit(Slash, guilds=[GUILD_ID], name="submit", parent=DuelParent):
    """Submit record to your duel."""

    screenshot: discord.Attachment = discord.Option(
        description="Screenshot of your record."
    )
    record: str = discord.Option(
        description="Your personal record. Format: HH:MM:SS.ss - You can omit the hours "
        "or minutes if they are 0. "
    )

    async def callback(self):
        await self.defer(ephemeral=True)

        duel = await Duel.find_duel(self.interaction.user.id)
        if not duel:
            raise TournamentStateError("You are not in a duel.")

        if not duel.player1.ready or not duel.player2.ready:
            raise TournamentStateError("Both players are not ready!")

        record_seconds = time_convert(self.record)
        await check_user(self.interaction.user)

        player = None
        if duel.player1.user_id == self.interaction.user.id:
            player = duel.player1
        elif duel.player2.user_id == self.interaction.user.id:
            player = duel.player2

        if player.record is None or player.record > record_seconds:
            player.record = record_seconds
            player.attachment_url = self.screenshot.url
        else:
            raise RecordNotFaster("Personal best needs to be faster to update.")

        embed = create_embed(
            title="New submission",
            desc=display_record(player.record),
            user=self.interaction.user,
        )
        embed.set_image(url=self.screenshot.url)
        view = RecordSubmitView()
        await self.interaction.edit_original_message(
            content="Is this correct?", view=view, embed=embed
        )
        await view.wait()

        if not view.confirm.value:
            return
        await duel.save()
        await self.interaction.guild.get_channel_or_thread(duel.thread).send(
            embed=embed
        )


class ForfeitDuel(Slash, guilds=[GUILD_ID], name="forfeit", parent=DuelParent):
    """Forfeit your duel and wager after the duel has started."""

    async def callback(self):
        await self.defer(ephemeral=True)

        duel = await Duel.find_duel(self.interaction.user.id)
        if not duel:
            raise TournamentStateError("You are not in a duel.")

        if not duel.player1.ready or not duel.player2.ready:
            raise TournamentStateError(
                "You can't forfeit a duel that hasn't started. "
                "Cancel the duel with the CANCEL button!"
            )

        view = RecordSubmitView()
        await self.interaction.edit_original_message(
            content="Do you want to forfeit your duel?",
            view=view,
        )
        await view.wait()
        if not view.confirm.value:
            return

        winner = None
        loser = None
        if duel.player1.user_id == self.interaction.user.id:
            loser = duel.player1.user_id
            winner = duel.player2.user_id
        elif duel.player2.user_id == self.interaction.user.id:
            loser = duel.player2.user_id
            winner = duel.player1.user_id

        await ExperiencePoints.duel_end(
            winner=winner,
            loser=loser,
            wager=duel.wager,
        )
        thread = self.interaction.guild.get_thread(duel.thread)
        msg = [m async for m in thread.history(limit=1, after=thread.created_at)][0]
        await msg.edit(content= f"{self.interaction.user.mention} forfeited and lost {duel.wager} XP!" + msg.content)
        await self.interaction.edit_original_message(
            content=f"Forfeit!",
            view=None,
        )
        await self.interaction.guild.get_thread(duel.thread).archive(locked=True)
        await duel.delete()


class DeleteDuel(Slash, guilds=[GUILD_ID], name="delete-record", parent=DuelParent):
    """Delete your duel record."""

    async def callback(self):
        await self.defer(ephemeral=True)

        duel = await Duel.find_duel(self.interaction.user.id)
        if not duel:
            raise TournamentStateError("You are not in a duel.")

        if not duel.player1.ready or not duel.player2.ready:
            raise TournamentStateError("Duel hasn't started.")

        player = None
        if duel.player1.user_id == self.interaction.user.id:
            player = duel.player1
        elif duel.player2.user_id == self.interaction.user.id:
            player = duel.player2

        view = RecordSubmitView()
        await self.interaction.edit_original_message(
            content="Do you want to delete your record?",
            view=view,
        )
        await view.wait()
        if not view.confirm.value:
            return
        player.record = None
        await duel.save()
        await self.interaction.edit_original_message(
            content="Deleted.",
            view=None,
        )
