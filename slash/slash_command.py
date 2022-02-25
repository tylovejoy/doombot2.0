import discord

class Slash(discord.SlashCommand):

    async def error(self, exception: Exception) -> None:
        await self.interaction.edit_original_message(
            content=exception,
        )