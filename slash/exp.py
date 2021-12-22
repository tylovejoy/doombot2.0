import io
from logging import getLogger
from math import ceil
from typing import Optional

import discord
from PIL import Image, ImageDraw, ImageFont
from discord.guild import MISSING

from database import ExperiencePoints
from slash.records import check_user
from utils import GUILD_ID

logger = getLogger(__name__)


def setup(bot):
    bot.application_command(RankCard)


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
    number = str(ceil(level % 20 / 4) + 1)
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


class RankCard(discord.SlashCommand, guilds=[GUILD_ID], name="rank"):
    """Display either your rank card or another users."""

    user: Optional[discord.Member] = discord.Option(
        description="Enter user to see their rank card. Leave this blank if you want to view your own."
    )

    async def callback(self) -> None:
        if self.user is MISSING:
            self.user = self.interaction.user

        search = await ExperiencePoints.find_one({"user_id": self.user.id})

        if not search:
            search = await check_user(self.interaction)

        user = self.user

        name = user.name[10:] + "#" + user.discriminator

        if search.alias:
            name = search.alias

        logo_fp = {
            "Unranked": "data/ranks/bronze.png",
            "Gold": "data/ranks/gold.png",
            "Diamond": "data/ranks/diamond.png",
            "Grandmaster": "data/ranks/grandmaster.png",
        }

        ta_logo = Image.open(logo_fp[search.rank.ta]).convert("RGBA")
        mc_logo = Image.open(logo_fp[search.rank.mc]).convert("RGBA")
        hc_logo = Image.open(logo_fp[search.rank.hc]).convert("RGBA")
        bo_logo = Image.open(logo_fp[search.rank.bo]).convert("RGBA")

        ta_logo.thumbnail((100, 100))
        mc_logo.thumbnail((100, 100))
        hc_logo.thumbnail((100, 100))
        bo_logo.thumbnail((100, 100))
        old_x = 15
        old_y = 66
        x = 1165
        y = 348
        y_offset = 10
        x_offset = 10
        inner_box = (0, 0, x, y)

        img = Image.new("RGBA", (x, y), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        rank_card = Image.open("data/rankcard.png").convert("RGBA")
        img.paste(rank_card)

        with io.BytesIO() as avatar_binary:
            await user.avatar.save(fp=avatar_binary)
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
        ta_box_xy = (375 + old_x - rank_x_offset, 98 + old_y // 2 - rank_y_offset)
        mc_box_xy = (508 + old_x - rank_x_offset, 98 + old_y // 2 - rank_y_offset)
        hc_box_xy = (641 + old_x - rank_x_offset, 98 + old_y // 2 - rank_y_offset)
        bo_box_xy = (774 + old_x - rank_x_offset, 98 + old_y // 2 - rank_y_offset)

        img.paste(ta_logo, ta_box_xy, ta_logo)
        img.paste(mc_logo, mc_box_xy, mc_logo)
        img.paste(hc_logo, hc_box_xy, hc_logo)
        img.paste(bo_logo, bo_box_xy, bo_logo)

        font_file = "data/fonts/segoeui.ttf"
        font2_file = "data/fonts/avenir.otf"
        # Username/Discriminator
        name_font = ImageFont.truetype(font2_file, 50)
        name_pos = x // 2 - d.textlength(name, font=name_font) // 2 + old_x
        d.text((name_pos, 170 + old_y // 2), name, fill=(255, 255, 255), font=name_font)

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
        xp_circle_r_pad = 100
        xp_circle_dia = 160

        place = 0
        all_users = await ExperiencePoints.find().sort("+xp").to_list()
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
        else:
            place_font_size = 100

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

        with io.BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await self.interaction.response.send_message("rankcard")
            await self.interaction.edit_original_message(
                content="", file=discord.File(fp=image_binary, filename="rank_card.png")
            )
