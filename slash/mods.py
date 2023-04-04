import io
from discord.utils import MISSING
from typing import List, Literal, Optional
import discord
from logging import getLogger
from database.documents import Voting
from utils.embed import create_embed
from utils.utilities import check_permissions, logging_util
from utils.constants import GUILD_ID, NEBULA
from slash.parents import ModParent
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from slash.slash_command import Slash
from views.roles import TherapyRole

logger = getLogger(__name__)


def setup(bot: discord.Client):
    logger.info(logging_util("Loading", "MODS"))
    bot.application_command(Sync)
    bot.application_command(TempCommand)


anonymity_convert = {
    "Anonymous": 0,
    "Private": 1,
    "Public": 2,
}


class Sync(Slash, name="sync", guilds=[GUILD_ID]):
    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        if self.interaction.user.id != NEBULA:
            await self.interaction.edit_original_message(
                content="Only nebula can use this command."
            )
            return
        await self.interaction.edit_original_message(content="Syncing")
        logger.info(logging_util("Uploading", "SLASH COMMANDS"))
        await self.client.upload_guild_application_commands()
        await self.client.upload_global_application_commands()
        logger.info(logging_util("Uploading Complete", "SLASH COMMANDS"))
        await self.interaction.edit_original_message(content="Done")


class TempCommand(Slash, name="temp", guilds=[GUILD_ID]):
    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        if self.interaction.user.id != NEBULA:
            await self.interaction.edit_original_message(
                content="Only nebula can use this command."
            )
            return
        await self.interaction.edit_original_message(content="Doing.")
        embed = create_embed("Serious Chat Access", "", "")
        view = TherapyRole()
        await self.interaction.guild.get_channel(752273327749464105).send(
            embed=embed, view=view
        )
        await self.interaction.edit_original_message(content="Done.")


class Vote(Slash, name="vote", guilds=[GUILD_ID], parent=ModParent):
    """Create a vote interface."""

    vote: str = discord.Option(description="Content of the vote.")
    anonymity: Literal["Anonymous", "Private", "Public"] = discord.Option(
        description="Type of results."
    )
    option_one: str = discord.Option(description="Option 1")
    option_two: str = discord.Option(description="Option 2")
    option_three: Optional[str] = discord.Option(description="Option 3")
    option_four: Optional[str] = discord.Option(description="Option 4")
    option_five: Optional[str] = discord.Option(description="Option 5")

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        await check_permissions(self.interaction)
        all_options = [
            self.option_one,
            self.option_two,
            self.option_three,
            self.option_four,
            self.option_five,
        ]
        options = []
        for x in all_options:
            if x in [MISSING, None]:
                break
            options.append(x)

        embed = create_embed(
            "Vote!",
            "You can change your vote, but you cannot cast multiple!\n\n" + self.vote,
            self.interaction.user,
        )

        message = await self.interaction.channel.send(embed=embed)
        view = VotingView(message, options)

        await message.edit(view=view)
        vote_document = Voting(
            message_id=message.id,
            channel_id=message.channel.id,
            user_id=self.interaction.user.id,
            anonymity=anonymity_convert[self.anonymity],
        )
        await vote_document.save()


class VotingView(discord.ui.View):
    """View for the voting interface."""

    def __init__(self, message: discord.Message, options: List[str]):
        super().__init__(timeout=None)
        self.message = message
        for option in options:
            self.add_item(VotingButton(option))
        self.add_item(EndVote())


class EndVote(discord.ui.Button):
    """Ends vote view."""

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="End Vote")

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view: VotingView

        document = await Voting.find_one(Voting.message_id == self.view.message.id)
        if not document or document.user_id != interaction.user.id:
            return

        await document.delete()
        self.view.clear_items()
        await self.view.message.edit(
            content=f"VOTE ENDED BY {interaction.user.mention}", view=self.view
        )
        self.view.stop()
        await self.create_results(interaction, document)

    @staticmethod
    async def create_results(
        interaction: discord.Interaction, document: Voting
    ) -> None:
        if document.anonymity == 0:
            return
        embed = create_embed(
            "Results",
            "",
            interaction.user,
        )
        for i, choice in enumerate(document.choices):
            user_str = ""
            for user, value in document.voters.items():
                if value == i:
                    user_str += f"<@{user}>\n"

            embed.add_field(name=choice, value=user_str or "No results", inline=False)

        if document.anonymity == 1:
            await interaction.user.send(embed=embed)

        elif document.anonymity == 2:
            await interaction.guild.get_channel(document.channel_id).send(embed=embed)


class VotingButton(discord.ui.Button):
    """A button for a specific vote."""

    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.gray, label=label[:80])

    async def callback(self, interaction: discord.Interaction):
        self.view: VotingView

        document = await Voting.find_one(Voting.message_id == self.view.message.id)
        if not document:
            return
        if str(interaction.user.id) in document.voters:
            document.choices[
                list(document.choices.keys())[document.voters[str(interaction.user.id)]]
            ] -= 1

        document.choices.update({self.label: document.choices.get(self.label, 0) + 1})
        document.voters.update(
            {str(interaction.user.id): list(document.choices.keys()).index(self.label)}
        )
        await document.save()

        image = await plot(
            list(document.choices.keys()), list(document.choices.values())
        )

        await self.view.message.edit(
            embed=self.view.message.embeds[0].set_image(
                url="attachment://vote_chart.png"
            ),
            file=image,
        )


async def plot(labels: List[str], values: List[int]):
    fig = plt.figure(figsize=(6, 5))
    plt.axes().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.bar(labels, values, color="black", width=0.4)
    plt.xlabel("Options")
    plt.ylabel("# of Votes")
    b = io.BytesIO()
    plt.savefig(b, format="png")
    plt.close()
    b.seek(0)
    return discord.File(b, filename="vote_chart.png")
