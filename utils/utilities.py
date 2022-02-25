import datetime
import re
from typing import Union

import discord

from database.maps import MapAlias
from utils.constants import (
    BONUS_ROLE_ID,
    BRACKET_TOURNAMENT_ROLE_ID,
    HC_ROLE_ID,
    MC_ROLE_ID,
    ROLE_WHITELIST,
    TA_ROLE_ID,
    TRIFECTA_ROLE_ID,
)
from utils.errors import InvalidTime

TIME_REGEX = re.compile(
    r"(?<!.)(\d{1,2})?:?(\d{1,2})?:?(?<!\d)(\d{1,2})\.?\d{1,4}?(?!.)"
)


def logging_util(first: str, second: str) -> str:
    return first + " " + "-" * (30 - len(first)) + " " + second + "..."


def is_time_format(s: str) -> bool:
    """Check if string is in HH:MM:SS.SS format or a legal variation."""
    return bool(TIME_REGEX.match(s))


def time_convert(time_input: str) -> float:
    """Convert time (str) into seconds (float)."""
    try:
        neg_time = -1 if time_input[0] == "-" else 1
        time_list = time_input.split(":")
        if len(time_list) == 1:
            return float(time_list[0])
        if len(time_list) == 2:
            return float((int(time_list[0]) * 60) + (neg_time * float(time_list[1])))
        if len(time_list) == 3:
            return float(
                (int(time_list[0]) * 3600)
                + (neg_time * (int(time_list[1]) * 60))
                + (neg_time * float(time_list[2]))
            )
    except Exception:
        raise InvalidTime("Record is not in the correct format! HH:MM:SS.ss")


def display_record(record: float, tournament: bool = False) -> str:
    """Display record in HH:MM:SS.ss format."""
    negative = "-" if is_negative(record) else ""
    dt = datetime.datetime.min + datetime.timedelta(seconds=abs(record))
    hour_remove = 0
    seconds_remove = -4

    if tournament:
        if dt.hour == 0 and dt.minute == 0:
            hour_remove = 6
        elif dt.hour == 0:
            hour_remove = 3
            if dt.minute < 10:
                hour_remove = 4

        if dt.microsecond == 0:
            seconds_remove = -7

    return negative + dt.strftime("%H:%M:%S.%f")[hour_remove:seconds_remove]


def is_negative(s: Union[float, int]) -> bool:
    """Check if a number is negative."""
    if s < 0:
        return True


def preprocess_map_code(map_code: str) -> str:
    """Converts map codes to acceptable format."""
    return map_code.upper().replace("O", "0")


async def find_alt_map_code(map_code: str) -> str:
    """Return a map code alias and a corresponding bool."""
    search = await MapAlias.get_alias(map_code)
    if search:
        return search, True
    return map_code, False


def case_ignore_compare(string1: str, string2: str) -> bool:
    """Compare two strings, case insensitive."""
    return string2.casefold() in string1.casefold()


async def check_permissions(interaction: discord.Interaction, additional_perms: bool = False) -> bool:
    if interaction.response.is_done():
        send = interaction.edit_original_message
    else:
        send = interaction.response.send_message

    if any(role.id in ROLE_WHITELIST for role in interaction.user.roles) or additional_perms:
        return True
   
    await send(content="You do not have permission to use this command.")
    return False


def check_roles(interaction: discord.Interaction) -> bool:
    """Check if user has whitelisted roles."""
    return any(role.id in ROLE_WHITELIST for role in interaction.user.roles)


def get_mention(category: str, interaction: discord.Interaction) -> str:
    """Get a role mention for each category selected."""
    role_id = None
    if category == "ta":
        role_id = TA_ROLE_ID
    elif category == "mc":
        role_id = MC_ROLE_ID
    elif category == "hc":
        role_id = HC_ROLE_ID
    elif category == "bo":
        role_id = BONUS_ROLE_ID
    elif category == "br":
        role_id = BRACKET_TOURNAMENT_ROLE_ID
    elif category == "tr":
        role_id = TRIFECTA_ROLE_ID

    return interaction.guild.get_role(role_id).mention


def star_emoji(stars: int) -> str:
    if 10 > stars >= 0:
        return "<:upper:929871697555914752>"
    elif 15 > stars >= 10:
        return "<:ds2:873791529876082758>"
    elif 20 > stars >= 15:
        return "<:ds3:873791529926414336>"
    else:
        return "<:ds4:873791530018701312>"


async def select_button_enable(
    view: discord.ui.View, select: discord.ui.Select
) -> None:
    if len(select.values):
        view.confirm.disabled = False
    else:
        view.confirm.disabled = True
    for x in select.options:
        if x.label in select.values:
            x.default = True
        else:
            x.default = False

    await view.interaction.edit_original_message(view=view)


async def no_perms_warning(interaction: discord.Interaction):
    await interaction.response.send_message(
        "You do not have permission to use this command.", ephemeral=True
    )


def tournament_category_map(category: str) -> str:
    return {
        "ta": "Time Attack",
        "mc": "Mildcore",
        "hc": "Hardcore",
        "bo": "Bonus",
        "general": "General",
    }.get(category, None)


def tournament_category_map_reverse(category: str) -> str:
    return {
        "Time Attack": "ta",
        "Mildcore": "mc",
        "Hardcore": "hc",
        "Bonus": "bo",
        "Trifecta": "tr",
        "Bracket": "br",
    }.get(category, None)


def format_missions(type_: str, target: Union[str, int, float]) -> str:
    """Format missions into user friendly strings."""
    formatted = ""
    # General missions
    if type_ == "xp":
        formatted += f"Get {target} XP (excluding missions)\n"
    elif type_ == "missions":
        formatted += f"Complete {target} missions\n"
    elif type_ == "top":
        formatted += f"Get Top 3 in {target} categories.\n"
    # Category Missions
    elif type_ == "sub":
        formatted += f"Get {type_} {display_record(float(target), tournament=True)}\n"
    elif type_ == "complete":
        formatted += "Complete the level.\n"

    return formatted


def make_ordinal(n):
    """
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    n = int(n)
    suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    return str(n) + suffix
