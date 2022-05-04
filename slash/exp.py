import io
from logging import getLogger
from math import ceil
from typing import Optional

import discord
from discord.utils import MISSING
from PIL import Image, ImageDraw, ImageFont

from database.documents import ExperiencePoints
from slash.parents import ModParent, TournamentParent
from slash.records import check_user
from slash.slash_command import Slash
from utils.constants import GUILD_ID
from utils.embed import create_embed, split_embeds, xp_embed_fields
from utils.errors import NameTooLong
from utils.utilities import check_roles, logging_util
from views.paginator import Paginator

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "EXP"))
    bot.application_command(RankCard)
    bot.application_command(Alerts)
    bot.application_command(ChangeName)
    bot.application_command(VerificationStats)
    bot.application_command(RankLeaderboard)
    bot.application_command(ToggleRecordSubmission)


def format_xp(xp):
    """Truncate/format numbers over 1000 to 1k format."""
    if 1000000 > xp > 999:
        xp = str(float(xp) / 1000)[:-2] + "k"
    elif xp > 1000000:
        xp = str(float(xp) / 1000000)[:-3] + "m"

    return str(xp)


def find_level(player_xp):
    """Find a player's level from their XP amount."""
    total = 0
    for level in range(101):
        total += 5 * (level ** 2) + (50 * level) + 100
        if total > player_xp:
            return level


def find_portrait(level) -> str:
    """Find which portrait to use."""
    number = str(ceil(level % 20 / 4))
    if number == "0":
        number = "1"
    if level <= 20:
        filename = "bronze" + number + ".png"
    elif 20 <= level < 40:
        filename = "silver" + number + ".png"
    elif 40 <= level < 60:
        filename = "gold" + number + ".png"
    elif 60 <= level < 80:
        filename = "platinum" + number + ".png"
    elif 80 <= level < 100:
        filename = "diamond" + number + ".png"
    else:
        filename = "diamond5.png"
    return filename


class RankLeaderboard(Slash, name="rank-leaderboard", guilds=[GUILD_ID]):
    """Display ranks leaderboard."""

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        embed = create_embed(
            "Ranks Leaderboard",
            "",
            self.interaction.user,
        )
        all_ranks = await ExperiencePoints.xp_leaderboard()
        embeds = await split_embeds(embed, all_ranks, xp_embed_fields)
        view = Paginator(embeds, self.interaction.user)
        await view.start(self.interaction)


LOGO_FILE_PATH = {
    "Unranked": "data/ranks/bronze.png",
    "Gold": "data/ranks/gold.png",
    "Diamond": "data/ranks/diamond.png",
    "Grandmaster": "data/ranks/grandmaster.png",
}


def open_logo(rank: str) -> Image:
    return Image.open(LOGO_FILE_PATH[rank]).convert("RGBA")


class RankCard(Slash, name="rank"):
    """Display either your rank card or another users."""

    user: Optional[discord.Member] = discord.Option(
        description="Enter user to see their rank card. Leave this blank if you want to view your own."
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)

        if self.user is MISSING:
            self.user = self.interaction.user

        search = await ExperiencePoints.find_one({"user_id": self.user.id})
        if not search:
            search = await check_user(self.interaction.user)

        user = self.user

        name = user.name[:18] + "#" + user.discriminator

        if search.alias:
            name = search.alias[:18]

        ta_logo = Image.open(LOGO_FILE_PATH[search.rank.ta]).convert("RGBA")
        mc_logo = Image.open(LOGO_FILE_PATH[search.rank.mc]).convert("RGBA")
        hc_logo = Image.open(LOGO_FILE_PATH[search.rank.hc]).convert("RGBA")
        # bo_logo = Image.open(LOGO_FILE_PATH[search.rank.bo]).convert("RGBA")

        ta_logo.thumbnail((100, 100))
        mc_logo.thumbnail((100, 100))
        hc_logo.thumbnail((100, 100))
        # bo_logo.thumbnail((100, 100))

        rank_card = Image.open("data/rankcard_bg_duels.png").convert("RGBA")

        old_x = 15
        old_y = 66
        x = rank_card.size[0]  # 1165 + 10
        y = rank_card.size[1]  # 348
        x_offset = 10

        img = Image.new("RGBA", (x, y), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")

        img.paste(rank_card)

        with io.BytesIO() as avatar_binary:
            await user.display_avatar.save(fp=avatar_binary)
            avatar = Image.open(avatar_binary).convert("RGBA")
            avatar.thumbnail((200, 200))
            av_mask = Image.new("L", avatar.size, 0)
            draw = ImageDraw.Draw(av_mask)
            draw.ellipse((0, 0, 200, 200), fill=255)
            a_height = avatar.size[1]
            img.paste(avatar, (x_offset * 4 + old_x, (y - a_height) // 2), av_mask)

        # Portrait PFP
        level = find_level(search.xp)
        portrait_file = find_portrait(level)
        portrait = Image.open("data/portraits/" + portrait_file).convert("RGBA")
        img.paste(portrait, (-60, -30), portrait)

        rank_x_offset = 50
        rank_y_offset = 37
        for x_val, logo in zip(
            [375, 508, 641, 774], [ta_logo, mc_logo, hc_logo]  # bo_logo]
        ):
            img.paste(
                logo,
                (x_val + old_x - rank_x_offset, 98 + old_y // 2 - rank_y_offset),
                logo,
            )

        font_file = "data/fonts/segoeui.ttf"
        font2_file = "data/fonts/avenir.otf"
        # Username/Discriminator
        name_font = ImageFont.truetype(font2_file, 50)
        name_pos = x // 2 - d.textlength(name, font=name_font) // 2 + old_x
        d.text((name_pos, 170 + old_y // 2), name, fill=(255, 255, 255), font=name_font)

        # W/L Duels
        duels_font = ImageFont.truetype(font_file, 30)
        losses = search.losses
        if losses is None:
            losses = 0
        wins = search.wins
        if wins is None:
            wins = 0
        wins = str(wins) + " W"
        losses = str(losses) + " L"
        wins_pos = 729 + (849 - 729) // 2 - d.textlength(wins, font=duels_font) // 2
        losses_pos = 729 + (849 - 729) // 2 - d.textlength(losses, font=duels_font) // 2

        # between 729 -> 849 is box
        d.text((wins_pos, 98), wins, fill=(255, 255, 255), font=duels_font)
        d.text((losses_pos, 138), losses, fill=(255, 255, 255), font=duels_font)

        # XP
        xp_font = ImageFont.truetype(font_file, 40)
        xp = format_xp(search.xp)
        xp_length = x // 2 - d.textlength(f"Total XP: {xp}", font=xp_font) // 2 + old_x
        d.text(
            (xp_length, 215 + old_y // 2),
            f"Total XP: {xp}",
            fill=(255, 255, 255),
            font=xp_font,
        )

        # Highest Position
        # xp_circle_r_pad = 100
        # xp_circle_dia = 160

        place = 0
        all_users = await ExperiencePoints.find().sort("-xp").to_list()
        for i, u in enumerate(all_users):
            if u.user_id == user.id:
                place = i + 1
        if place == 1:
            pos_portrait_f = "gold_position.png"
        elif place == 2:
            pos_portrait_f = "silver_position.png"
        elif place == 3:
            pos_portrait_f = "bronze_position.png"
        else:
            pos_portrait_f = "no_position.png"

        color = (9, 10, 11, 255)

        place_circle_x1 = x - (x_offset * 4) - 200 - 5
        place_circle_x2 = x - (x_offset * 4) + 5
        place_circle_y1 = (y - 200) // 2 - 5
        place_circle_y2 = (y - 200) // 2 + 200 + 5

        d.ellipse(
            (place_circle_x1, place_circle_y1, place_circle_x2, place_circle_y2),
            fill=color,
        )

        if len(str(place)) == 1:
            place_font_size = 120
        elif len(str(place)) == 2:
            place_font_size = 110
        elif place < 999:
            place_font_size = 100
        else:
            place_font_size = 85

        place_font = ImageFont.truetype(font_file, place_font_size)

        place_x = (
            place_circle_x1
            + (place_circle_x2 - place_circle_x1) // 2
            - d.textlength(str(place), font=place_font) // 2
        )

        ascent, _ = place_font.getmetrics()
        (_, _), (_, offset_y) = place_font.font.getsize(str(place))

        place_y = y // 2 - (ascent - offset_y)

        d.text(
            (place_x, place_y), str(place), fill=(255, 255, 255, 255), font=place_font
        )

        pos_portrait = Image.open("data/portraits/" + pos_portrait_f).convert("RGBA")
        img.paste(pos_portrait, (x - 350, -28), pos_portrait)

        width, height = img.size
        img = img.resize((width // 2, height // 2))

        with io.BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await self.interaction.edit_original_message(
                content="", file=discord.File(fp=image_binary, filename="rank_card.png")
            )


class Alerts(Slash, name="alerts"):
    """Enable/disable verification alerts."""

    value: bool = discord.Option(
        description="Turn alerts on or off.",
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        user = await ExperiencePoints.find_user(self.interaction.user.id)

        if self.value:
            user.alerts_enabled = True
        else:
            user.alerts_enabled = False

        await self.interaction.edit_original_message(
            content=f"Alerts turned {'on' if self.value else 'off'}."
        )
        await user.save()


class ChangeName(Slash, name="name"):
    """Change your display name for DoomBot commands."""

    name: str = discord.Option(
        description="What should your display name be?",
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        if len(self.name) > 25:
            raise NameTooLong("Name must be less than 25 characters.")

        user = await ExperiencePoints.find_user(self.interaction.user.id)
        user.alias = self.name
        await self.interaction.edit_original_message(
            content=f"Name changed to {self.name}."
        )
        await user.save()


class VerificationStats(Slash, name="verified"):
    """Display how many records a user has verified."""

    user: discord.Member = discord.Option(
        description="Enter a use to see their verification stats."
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        user = await ExperiencePoints.find_user(self.user.id)

        embed = create_embed(
            f"Verification Stats for {self.user}",
            f"# of Records Verified: **{user.verified_count}**",
            self.interaction.user,
        )

        await self.interaction.edit_original_message(embed=embed)


class ToggleRecordSubmission(Slash, name="autosubmit", parent=TournamentParent):
    """Toggle autosubmission of tournament records."""

    value: bool = discord.Option(
        description="True, if you want your submissions to be automatically added."
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        user = await ExperiencePoints.find_user(self.interaction.user.id)
        setattr(user, "dont_submit", not self.value)
        await self.interaction.edit_original_message(
            content=f"Autosubmission changed to {self.value}."
        )
        await user.save()


class TherapyBan(Slash, name="therapy-ban", parent=ModParent):
    """Ban a user from using the therapy command."""

    user: discord.Member = discord.Option(
        description="Enter a user to ban from using the therapy command."
    )

    value: bool = discord.Option(
        description="True, if you want to ban the user from using the therapy command."
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        check_roles(self.interaction)
        user = await ExperiencePoints.find_user(self.user.id)
        setattr(user, "therapy_banned", self.value)
        status = "banned" if self.value else "unbanned"
        await self.interaction.edit_original_message(
            content=f"{self.user} has been {status} from using the therapy channel."
        )
        await user.save()
