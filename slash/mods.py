import io
from discord.utils import MISSING
from typing import List, Optional
import discord
from logging import getLogger
from database.documents import Voting
from utils.embed import create_embed
from utils.utilities import check_permissions, logging_util
from utils.constants import GUILD_ID
from slash.parents import ModParent
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from slash.slash_command import Slash

logger = getLogger(__name__)

def setup(bot: discord.Client):
    logger.info(logging_util("Loading", "MODS"))

class Vote(Slash, name="vote", guilds=[GUILD_ID], parent=ModParent):
    """Create a vote interface."""

    vote: str = discord.Option(description="Content of the vote.")
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
            "Be careful, you can only vote _once_!\n\n" + self.vote,
            self.interaction.user
        )

        message = await self.interaction.channel.send(embed=embed)
        view = VotingView(message, options)
        
        await message.edit(view=view)
        vote_document = Voting(message_id=message.id)
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
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="End Vote (MOD Only)"
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view: VotingView
        await check_permissions(interaction)
        await self.view.message.edit(content="VOTE ENDED.")
        document = await Voting.find_one(Voting.message_id == self.view.message.id)
        if not document:
            return
        await document.delete()
        self.view.stop()


class VotingButton(discord.ui.Button):
    """A button for a specific vote."""

    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.gray, label=label[:80])

    async def callback(self, interaction: discord.Interaction):
        self.view: VotingView

        document = await Voting.find_one(Voting.message_id == self.view.message.id)
        if not document:
            return
        if interaction.user.id in document.voters:
            return
        
        document.choices.update(
            {self.label: document.choices.get(self.label, 0) + 1}
        )
        document.voters.append(interaction.user.id)
        await document.save()

        image = await plot(list(document.choices.keys()), list(document.choices.values()))

        await self.view.message.edit(
            embed=self.view.message.embeds[0].set_image(
                url="attachment://vote_chart.png"
            ), 
            file=image,
        )



async def plot(labels: List[str], values: List[int]):
    fig = plt.figure(figsize = (6, 5))
    plt.axes().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.bar(
        labels, 
        values, 
        color ='black',
        width = 0.4
    )
    plt.xlabel("Options")
    plt.ylabel("# of Votes")    
    b = io.BytesIO()
    plt.savefig(b, format='png')
    plt.close()
    b.seek(0)
    return discord.File(b, filename="vote_chart.png")
