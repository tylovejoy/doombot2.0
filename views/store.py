from lib2to3.refactor import MultiprocessRefactoringTool
import discord

from views.basic import ConfirmButton


class MainStoreView(discord.ui.View):
    """Main menu of the store."""

    def __init__(self, interaction: discord.Interaction, **kwargs):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.main_embed = kwargs.get("main")
        self.emotes_embed = kwargs.get("emotes")
        self.roles_embed = kwargs.get("roles")
        self.emote_dropdown = StoreDropdown(
            ["Standard Emoji", "Animated Emoji", "Sticker"]
        )

        self.roles = StoreButton("Roles", self.roles_embed)
        self.emotes = StoreButton("Emotes", self.emotes_embed)
        self.back = StoreBack()
        self.confirm = ConfirmButton()
        self.main_menu_buttons = [self.roles, self.emotes]
        for item in self.main_menu_buttons:
            self.add_item(item)

    async def start(self):
        await self.interaction.edit_original_message(embed=self.main_embed, view=self)


class StoreButton(discord.ui.Button):
    def __init__(self, label, embed, row=0):
        self.view: MainStoreView
        self.embed = embed
        super().__init__(label=label, style=discord.ButtonStyle.blurple, row=row)

    async def callback(self, interaction: discord.Interaction):
        for item in self.view.main_menu_buttons:
            self.view.remove_item(item)
        self.view.add_item(self.view.confirm)
        self.view.add_item(self.view.back)
        self.view.add_item(self.view.emote_dropdown)
        await self.view.interaction.edit_original_message(
            embed=self.embed, view=self.view
        )


class StoreBack(discord.ui.Button):
    def __init__(self, row=0):
        self.view: MainStoreView
        super().__init__(label="Back", style=discord.ButtonStyle.grey, row=row)

    async def callback(self, interaction: discord.Interaction):
        for item in self.view.main_menu_buttons:
            self.view.add_item(item)
        self.view.remove_item(self)
        await self.view.interaction.edit_original_message(
            embed=self.view.main_embed, view=self.view
        )


class StoreDropdown(discord.ui.Select):
    def __init__(self, values):
        super().__init__()

        for value in values:
            self.add_option(
                label=value,
                value=value,
            )

    async def callback(self, interaction: discord.Interaction):
        return await super().callback(interaction)
