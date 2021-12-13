import discord
from database.documents import ExperiencePoints, Record
from utils.enum import Emoji
from utils.utils import display_record

from views.basic import ConfirmButton
from utils.constants import GUILD_ID, NON_SPR_RECORDS_ID, ROLE_WHITELIST, SPR_RECORDS_ID, VERIFICATION_CHANNEL_ID


class RecordSubmitView(discord.ui.View):
    def __init__(self, *, timeout=None, confirm_disabled=False):
        super().__init__(timeout=timeout)

        self.confirm = ConfirmButton(row=1, disabled=confirm_disabled)
        self.add_item(self.confirm)



class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)



    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not any(
            role.id in ROLE_WHITELIST
            for role in interaction.user.roles
        ):
            return False
        return True

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
    async def verify(self, button: discord.ui.Button, interaction: discord.Interaction):
        
        search = await Record.find_one(Record.hidden_id == interaction.message.id)

        try:
            spr = await interaction.guild.get_channel(SPR_RECORDS_ID).fetch_message(search.message_id)
        except Exception:
            spr = None
        try:
            n_spr = await interaction.guild.get_channel(NON_SPR_RECORDS_ID).fetch_message(search.message_id)
        except Exception:
            n_spr = None
        orig_message = spr or n_spr

        await orig_message.edit(content=f"{Emoji.VERIFIED} Verified!")
        if await ExperiencePoints.is_alertable(search.posted_by):
            user = interaction.guild.get_member(search.posted_by)
            await user.send(
                f"**Map Code:** {search.code}\n**Level name:** {search.level}\n**Record:** {display_record(search.record)}\n"
                f"Your record got {Emoji.VERIFIED} verified!\n\n"
                "Don't like these alerts? Turn it off by using the command `/alerts false`.\n"
                "You can change your display name for records in the bot with the command `/name`!"
            )
        
        try:
            hidden_msg = await interaction.guild.get_channel(VERIFICATION_CHANNEL_ID).fetch_message(search.hidden_id)
            await hidden_msg.delete()
        except discord.HTTPException:
            pass

        search.verified = True
        await search.save()
        self.stop()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, button: discord.ui.Button, interaction: discord.Interaction):
        orig_msg = interaction.original_message
        search = await Record.find_one(Record.hidden_id == interaction.message.id)
        await orig_msg.edit(content=f"{Emoji.NOT_VERIFIED} Rejected!")
        if await ExperiencePoints.is_alertable(search.posted_by):
            user = interaction.guild.get_member(search.posted_by)
            await user.send(
                f"**Map Code:** {search.code}\n**Level name:** {search.level}\n**Record:** {display_record(search.record)}\n"
                f"Your record got {Emoji.NOT_VERIFIED} rejected by {interaction.user.mention}!\n"
                "Usually, this happens when the level, record, or code was input incorrectly. Try again!\n\n"
                "Don't like these alerts? Turn it off by using the command `/alerts false`.\n"
                "You can change your display name for records in the bot with the command `/name`!"
            )
        try:
            hidden_msg = await interaction.guild.get_channel(VERIFICATION_CHANNEL_ID).fetch_message(search.hidden_id)
            await hidden_msg.delete()
        except discord.HTTPException:
            pass

        search.verified = False
        await search.save()
        self.stop()
