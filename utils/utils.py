import re
from database.documents import ExperiencePoints
import datetime


TIME_REGEX = re.compile(
    r"(?<!.)(\d{1,2})?:?(\d{1,2})?:?(?<!\d)(\d{1,2})\.?\d{1,4}?(?!.)"
)


def is_time_format(s):
    """Check if string is in HH:MM:SS.SS format or a legal variation."""
    return bool(TIME_REGEX.match(s))


def time_convert(time_input):
    """Convert time (str) into seconds (float)."""
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
    return


def display_record(record):
    """Display record in HH:MM:SS.SS format."""
    if check_negative(record):
        return format_timedelta(record)
    if str(datetime.timedelta(seconds=record)).count(".") == 1:
        return str(datetime.timedelta(seconds=record))[: -4 or None]
    return str(datetime.timedelta(seconds=record)) + ".00"


def check_negative(s):
    try:
        f = float(s)
        if f < 0:
            return True
        # Otherwise return false
        return False
    except ValueError:
        return False


def format_timedelta(td):
    if datetime.timedelta(seconds=td) < datetime.timedelta(0):
        return "-" + format_timedelta(-1 * td)
    return str(td)
