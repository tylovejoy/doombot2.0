import datetime

import discord
from discord.ui import TextInput

from utils.utilities import (
    get_mention,
    select_button_enable,
    tournament_category_map_reverse,
)
from views.basic import ConfirmButton
from database.tournament import Duel


class TournamentAnnouncementModal(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="Tournament Announcement Wizard")
        self.done = False
        self.title_ = None
        self.content = None
        self.interaction = None
        self.add_item(TextInput(label="Title"))
        self.add_item(
            TextInput(
                label="Announcement Content",
                style=discord.TextInputStyle.long,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Please wait...", ephemeral=True)
        self.interaction = interaction
        self.done = True
        self.title_ = self.children[0].value
        self.content = self.children[1].value


class TournamentStartModal(discord.ui.Modal):
    def __init__(self, category: str) -> None:
        super().__init__("Tournament Submit Wizard")
        self.category = category
        self.add_item(TextInput(label="Map Code"))
        self.add_item(TextInput(label="Level Name"))
        self.add_item(TextInput(label="Map Creator"))
        self.code = None
        self.level = None
        self.creator = None

    async def callback(self, interaction: discord.Interaction):

        self.code = self.children[0].value
        self.level = self.children[1].value
        self.creator = self.children[2].value
        await interaction.response.send_message(
            f"{self.category} set.\nCode: {self.code}\nLevel: {self.level}\nCreator: {self.creator}",
            ephemeral=True,
        )


class TournamentStartView(discord.ui.View):
    """View for Tournament Start wizard."""

    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.confirm_button = ConfirmButton(row=1)
        self.interaction = interaction
        self.ta_modal = None
        self.mc_modal = None
        self.hc_modal = None
        self.bo_modal = None
        self.bracket = False

    @discord.ui.button(
        label="Bracket Toggle Off", style=discord.ButtonStyle.grey, row=0
    )
    async def bracket_toggle(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.bracket = not self.bracket
        toggles = (
            ("On", discord.ButtonStyle.blurple)
            if self.bracket
            else ("Off", discord.ButtonStyle.grey)
        )
        button.label = f"Bracket Toggle {toggles[0]}"
        button.style = toggles[1]
        await self.interaction.edit_original_message(view=self)

    @discord.ui.button(label="TA", style=discord.ButtonStyle.red, row=1)
    async def ta(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Time Attack button."""
        button.style = discord.ButtonStyle.green
        self.ta_modal = TournamentStartModal("Time Attack")
        await interaction.response.send_modal(self.ta_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="MC", style=discord.ButtonStyle.red, row=1)
    async def mc(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Mildcore button."""
        button.style = discord.ButtonStyle.green
        self.mc_modal = TournamentStartModal("Mildcore")
        await interaction.response.send_modal(self.mc_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="HC", style=discord.ButtonStyle.red, row=1)
    async def hc(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Hardcore button."""
        button.style = discord.ButtonStyle.green
        self.hc_modal = TournamentStartModal("Hardcore")
        await interaction.response.send_modal(self.hc_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="BO", style=discord.ButtonStyle.red, row=1)
    async def bo(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Bonus button."""
        button.style = discord.ButtonStyle.green
        self.bo_modal = TournamentStartModal("Bonus")
        await interaction.response.send_modal(self.bo_modal)
        await self.enable_accept_button()

    async def enable_accept_button(self):
        """Enable confirm button when other buttons are pressed."""
        if any(
            [
                x is discord.ButtonStyle.green
                for x in [self.bo.style, self.ta.style, self.mc.style, self.hc.style]
            ]
        ):
            self.add_item(self.confirm_button)
        await self.interaction.edit_original_message(view=self)


class TournamentCategoryView(discord.ui.View):
    """View for selecting tournament mentions."""

    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.mentions = []
        self.interaction = interaction
        self.select = TournamentCategoriesSelect()
        self.add_item(self.select)

        self.confirm = ConfirmButton(row=1, disabled=True)
        self.add_item(self.confirm)

    async def start(self, embed) -> str:
        await self.interaction.edit_original_message(
            content="Select any mentions and confirm data is correct.",
            embed=embed,
            view=self,
        )
        await self.wait()
        return "".join(
            [
                get_mention(tournament_category_map_reverse(m), self.interaction)
                for m in self.mentions
            ]
        )


class TournamentCategoriesSelect(discord.ui.Select):
    """Tournament categories."""

    def __init__(self):
        super().__init__(
            placeholder="Choose which roles to be mentioned...",
            min_values=0,
            max_values=6,
            options=[
                discord.SelectOption(label="Time Attack", value="Time Attack"),
                discord.SelectOption(label="Mildcore", value="Mildcore"),
                discord.SelectOption(label="Hardcore", value="Hardcore"),
                discord.SelectOption(label="Bonus", value="Bonus"),
                discord.SelectOption(label="Trifecta", value="Trifecta"),
                discord.SelectOption(label="Bracket", value="Bracket"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        """Callback for tournament categories dropdown."""
        self.view.mentions = self.values
        await select_button_enable(self.view, self)


class DuelReadyView(discord.ui.View):
    """"""

    def __init__(self, original_interaction):
        super().__init__(timeout=43200)
        self.original_interaction = original_interaction
        self.message = None

    @discord.ui.button(label="READY UP", style=discord.ButtonStyle.green)
    async def ready(self, button: discord.ui.Button, interaction: discord.Interaction):
        duel = await Duel.find_duel_thread(interaction.user.id, interaction.channel_id)
        if not duel:
            await interaction.user.send("You are not in this duel!")
            return
        duel.end_time = discord.utils.utcnow() + datetime.timedelta(hours=24)
        await self.message.edit(
            content=(
                self.message.content
                + "\n\nReady, _set_, ***GO***!\n\nGet your best time by: \n"
                f"{discord.utils.format_dt(duel.end_time)} | "
                f"{discord.utils.format_dt(duel.end_time, style='R')}"
            ),
            view=None,
        )
        await duel.save()

    @discord.ui.button(label="CANCEL", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        duel = await Duel.find_duel_thread_two_players(
            interaction.user.id, interaction.channel_id
        )
        if not duel:
            await interaction.user.send("You are not in this duel!")
            return
        await duel.delete()
        await self.message.edit(content="CANCELLED!", view=None)

    async def on_timeout(self):
        duel = await Duel.find_duel_thread_only(self.message.channel.id)
        await duel.delete()
        await self.message.edit(
            content="CANCELLED, Player 2 did not ready up!", view=None
        )
