import discord

from database.documents import ExperiencePoints
from database.records import Record
from utils.constants import NON_SPR_RECORDS_ID, SPR_RECORDS_ID
from utils.enums import Emoji
from utils.records import delete_hidden
from utils.utilities import display_record
from views.basic import ConfirmButton


class RecordSubmitView(discord.ui.View):
    """View for record submissions."""

    def __init__(self, *, timeout=None, confirm_disabled=False):
        """Init view."""
        super().__init__(timeout=timeout)

        self.confirm = ConfirmButton(row=1, disabled=confirm_disabled)
        self.add_item(self.confirm)


class VerificationView(discord.ui.View):
    """View for verification notifications."""

    def __init__(self):
        """Init view."""
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify", style=discord.ButtonStyle.green, custom_id="v_verify"
    )
    async def verify(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Button component for verification acceptance."""
        await verification(interaction, True)
        self.stop()

    @discord.ui.button(
        label="Reject", style=discord.ButtonStyle.red, custom_id="v_reject"
    )
    async def reject(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Button component for verification rejection."""
        await verification(interaction, False)
        self.stop()


async def verification(interaction: discord.Interaction, verified: bool):
    """Verify a record."""
    search = await Record.find_one(Record.hidden_id == interaction.message.id)
    orig_message = await find_orig_msg(interaction, search)

    if verified:
        data = accepted(interaction, search)
        verifier = await ExperiencePoints.find_user(interaction.user.id)
        await verifier.increment_verified()
    else:
        data = rejected(interaction, search)

    await orig_message.edit(content=data["edit"])
    await orig_message.add_reaction(emoji=Emoji.UPPER)

    if await ExperiencePoints.is_alertable(search.user_id):
        user = interaction.guild.get_member(search.user_id)
        await user.send(data["direct_message"])
    await delete_hidden(interaction, search)
    search.verified = data["bool"]
    await search.save()


async def find_orig_msg(interaction, search: Record):
    """Try to fetch message from either Records channel."""
    try:
        spr = await interaction.guild.get_channel(SPR_RECORDS_ID).fetch_message(
            search.message_id
        )
    except (discord.NotFound, discord.HTTPException):
        spr = None
    try:
        n_spr = await interaction.guild.get_channel(NON_SPR_RECORDS_ID).fetch_message(
            search.message_id
        )
    except (discord.NotFound, discord.HTTPException):
        n_spr = None
    orig_message = spr or n_spr
    return orig_message


def accepted(interaction: discord.Interaction, search: Record) -> dict:
    """Data for verified records."""
    return {
        "edit": f"{Emoji.VERIFIED} Verified by {interaction.user.mention}!",
        "direct_message": (
            f"**Map Code:** {search.code}\n"
            f"**Level name:** {search.level}\n"
            f"**Record:** {display_record(search.record)}\n"
            f"Your record got {Emoji.VERIFIED} verified by {interaction.user.mention}!\n\n"
            + ALERT
        ),
        "bool": True,
    }


def rejected(interaction: discord.Interaction, search: Record) -> dict:
    """Data for rejected records."""
    return {
        "edit": f"{Emoji.NOT_VERIFIED} Rejected by {interaction.user.mention}!",
        "direct_message": (
            f"**Map Code:** {search.code}\n"
            f"**Level name:** {search.level}\n"
            f"**Record:** {display_record(search.record)}\n"
            f"Your record got {Emoji.NOT_VERIFIED} rejected by {interaction.user.mention}!\n"
            "Usually, this happens when the level, record, or code was input incorrectly. Try again!\n\n"
            + ALERT
        ),
        "bool": False,
    }


ALERT = (
    "Don't like these alerts? Turn it off by using the command `/alerts false`.\n"
    "You can change your display name for records in the bot with the command `/name`!"
)
