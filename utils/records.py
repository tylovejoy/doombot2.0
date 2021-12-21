import discord

from utils import VERIFICATION_CHANNEL_ID


async def delete_hidden(interaction, record_document):
    try:
        hidden_msg = await interaction.guild.get_channel(
            VERIFICATION_CHANNEL_ID
        ).fetch_message(record_document.hidden_id)
        await hidden_msg.delete()
    except (discord.NotFound, discord.HTTPException):
        pass
