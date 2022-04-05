from typing import List
import discord

from database.documents import ColorRoles, ExperiencePoints


async def add_remove_roles(interaction: discord.Interaction, role):
    if role in interaction.user.roles:
        await interaction.user.remove_roles(role)
        await interaction.response.send_message(
            content=f"Removed {role.name} role.",
            ephemeral=True,
        )
    else:
        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            content=f"Added {role.name} role.",
            ephemeral=True,
        )


class ColorSelect(discord.ui.Select):
    def __init__(self, options: List[ColorRoles]):
        super().__init__(
            custom_id="colors",
        )
        self.add_option(
            label="None",
            value="None",
            description="Remove color role.",
        )
        for option in options:
            self.add_option(
                label=option.label,
                value=str(option.role_id),
                emoji=option.emoji
            )
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        all_roles = [interaction.guild.get_role(int(role.value)) for role in self.options if role.value != "None"]
        
        for role in all_roles:
            await interaction.user.remove_roles(role)

        if self.values[0] == "None":
            await interaction.response.send_message(
                content="Removed color role.",
                ephemeral=True,
            )
            return
        
        await interaction.response.send_message(
            content="Added color role.",
            ephemeral=True,
        )
        await interaction.user.add_roles(
            interaction.guild.get_role(int(self.values[0]))
        )




class ColorRolesView(discord.ui.View):
    """Persistent reaction color roles."""

    def __init__(self, options):
        super().__init__(timeout=None)
        self.select = ColorSelect(options)
        self.add_item(self.select)



class ServerRelatedPings(discord.ui.View):
    """Persistent reaction server related roles."""

    def __init__(self):
        super().__init__(timeout=None)
        
    
    @discord.ui.button(
        label="Announcements",
        style=discord.ButtonStyle.blurple,
        custom_id="announcements",
    )
    async def announcements(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(802259719229800488)
        await add_remove_roles(interaction, role)

    @discord.ui.button(
        label="EU Sleep Ping",
        style=discord.ButtonStyle.grey,
        custom_id="eu_sleep_ping",
        row=1,
    )
    async def eu_ping(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(805542050060828682)
        await add_remove_roles(interaction, role)
    
    @discord.ui.button(
        label="NA Sleep Ping",
        style=discord.ButtonStyle.grey,
        custom_id="na_sleep_ping",
        row=1,
    )
    async def na_ping(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(808478386825330718)
        await add_remove_roles(interaction, role)

    @discord.ui.button(
        label="Asia Sleep Ping",
        style=discord.ButtonStyle.grey,
        custom_id="asia_sleep_ping",
        row=1,
    )
    async def asia_ping(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(874438907763228743)
        await add_remove_roles(interaction, role)
    
    @discord.ui.button(
        label="OCE Sleep Ping",
        style=discord.ButtonStyle.grey,
        custom_id="oce_sleep_ping",
        row=1,
    )
    async def oce_ping(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(937726966080094229)
        await add_remove_roles(interaction, role)

    @discord.ui.button(
        label="Movie Night",
        style=discord.ButtonStyle.grey,
        custom_id="movie_night",
        row=2,
    )
    async def movie_night(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(903667495922180167)
        await add_remove_roles(interaction, role)

    @discord.ui.button(
        label="Game Night",
        style=discord.ButtonStyle.grey,
        custom_id="game_night",
        row=2,
    )
    async def game_night(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(903667578549968896)
        await add_remove_roles(interaction, role)

    
class PronounRoles(discord.ui.View):
    """Persistent reaction server related roles."""

    def __init__(self):
        super().__init__(timeout=None)
        
    
    @discord.ui.button(
        label="They/Them",
        style=discord.ButtonStyle.grey,
        custom_id="they_pronoun",
    )
    async def they(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(884346785949167616)
        await add_remove_roles(interaction, role)

    @discord.ui.button(
        label="She/Her",
        style=discord.ButtonStyle.grey,
        custom_id="she_pronoun",
    )
    async def she(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(884346748334653481)
        await add_remove_roles(interaction, role)

    @discord.ui.button(
        label="He/Him",
        style=discord.ButtonStyle.grey,
        custom_id="he_pronoun",
    )
    async def he(self, item, interaction: discord.Interaction):
        role = interaction.guild.get_role(884346610652446720)
        await add_remove_roles(interaction, role)


class TherapyRole(discord.ui.View):
    """Persistent reaction server related roles."""

    def __init__(self):
        super().__init__(timeout=None)
        
    
    @discord.ui.button(
        label="Therapy",
        style=discord.ButtonStyle.green,
        custom_id="therapy",
    )
    async def therapy_access(self, item, interaction: discord.Interaction):

        user = await ExperiencePoints.find_user(interaction.user.id)
        if getattr(user, "therapy_banned", None):
            await interaction.response.send_message(
                ephemeral=True,
                content="You are banned from therapy. Please contact a staff member for more information.",
            )
            return
        role = interaction.guild.get_role(815041888566116422)
        await add_remove_roles(interaction, role)