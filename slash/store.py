from typing import Literal

import discord
from utils.embed import create_embed

from utils.constants import GUILD_ID
from views.store import MainStoreView


def setup(bot):
    bot.application_command(OpenStore)


class OpenStore(discord.SlashCommand, guilds=[GUILD_ID], name="store"):
    """View the XP store."""

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        main_menu = create_embed(
            "Doombot General Store",
            "Welcome! Select any of the buttons below to browse the store.",
            self.interaction.user,
        )
        emote_store = create_embed(
            "Emotes",
            "Here you can buy emote/sticker slots.",
            self.interaction.user,
        )
        role_store = create_embed(
            "Roles",
            "Here you can buy custom roles.",
            self.interaction.user,
        )
        view = MainStoreView(
            self.interaction, emotes=emote_store, roles=role_store, main=main_menu
        )
        await view.start()

        await view.wait()

        if not view.confirm.value:
            return

        await self.interaction.edit_original_message(
            content="Check your DMs to continue the transaction.", embed=None, view=None
        )

        if view.emote_dropdown.values[0] == "Standard Emoji":
            ...
        await self.interaction.user.send(
            "Respond with the emoji/sticker that you want to add.\n"
            "Image must be `PNG`, `JPG`, or `GIF`. All other file types/messages will be ignored!"
        )

        def emoji_check(message: discord.Message):
            return (
                message.guild == None
                and message.author.id == self.interaction.user.id
                and message.attachments
                and message.attachments[0].content_type
                in ["image/jpeg", "image/png", "image/gif"]
            )

        emoji = await self.client.wait_for("message", check=emoji_check, timeout=60)
        if not emoji:
            return

        emoji = emoji.attachments[0]

        await self.interaction.user.send(
            "Respond with the name that you want to give the emoji/sticker."
        )

        def name_check(message: discord.Message):
            return (
                message.guild == None and message.author.id == self.interaction.user.id
            )

        name = await self.client.wait_for("message", check=name_check, timeout=60)
        if not name:
            return

        name = name.content

        await self.interaction.user.send(f"Emoji name: {name}\n{emoji.url}")
