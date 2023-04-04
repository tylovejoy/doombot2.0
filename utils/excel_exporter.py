import operator
from logging import getLogger
from math import ceil

import xlsxwriter

from database.documents import ExperiencePoints
from database.tournament import Tournament, TournamentData

logger = getLogger(__name__)


async def init_workbook(tournament: Tournament):
    workbook = xlsxwriter.Workbook("DPK_Tournament.xlsx")
    grandmaster_ws = workbook.add_worksheet(name="Grandmaster")
    diamond_ws = workbook.add_worksheet(name="Diamond")
    gold_ws = workbook.add_worksheet(name="Gold")
    unranked_ws = workbook.add_worksheet(name="Unranked")
    missions_ws = workbook.add_worksheet(name="Missions")

    ranks = [grandmaster_ws, diamond_ws, gold_ws, unranked_ws]

    # Set up

    for worksheet in ranks:
        # Rank titles
        merge_format = workbook.add_format(
            {"align": "center", "bg_color": "#93c47d", "border": 1}
        )
        worksheet.merge_range("A1:C1", "Time Attack", merge_format)
        merge_format = workbook.add_format(
            {"align": "center", "bg_color": "#ff9900", "border": 1}
        )
        worksheet.merge_range("E1:G1", "Mildcore", merge_format)
        merge_format = workbook.add_format(
            {"align": "center", "bg_color": "#ff0000", "border": 1}
        )
        worksheet.merge_range("I1:K1", "Hardcore", merge_format)
        merge_format = workbook.add_format(
            {"align": "center", "bg_color": "#ffff00", "border": 1}
        )
        worksheet.merge_range("M1:O1", "Bonus", merge_format)
        # Name, Time, Points titles
        worksheet.write_row(
            "A2",
            ["Name", "Time", "Points", None] * 4,
            cell_format=workbook.add_format({"align": "left", "border": 1}),
        )
        worksheet.set_column_pixels(0, 15, width=105)
        worksheet.write(1, 3, "", workbook.add_format({"border": 0}))
        worksheet.write(1, 7, "", workbook.add_format({"border": 0}))
        worksheet.write(1, 11, "", workbook.add_format({"border": 0}))
        worksheet.write(1, 15, "", workbook.add_format({"border": 0}))

    # Format missions worksheet
    missions_ws.write_row(
        'A1',
        [
            "Names",
            "Easy",
            "Medium",
            "Hard",
            "Expert",
            "General",
            "Missions Total",
            "Total XP",
            "TA Average XP",
            "MC Average XP",
            "HC Average XP",
            "BO Average XP",
        ],
        cell_format=workbook.add_format({"border": 1}),
    )
    center_fmt = workbook.add_format({"align": "center"})

    missions_ws.set_column_pixels(0, 19, width=105)
    missions_ws.set_column(1, 5, cell_format=center_fmt)
    for i, (user_id, data) in enumerate(tournament.xp.items(), start=2):
        user = await ExperiencePoints.find_user(user_id)
        missions_total = (
            data["easy"] * 500
            + data["medium"] * 1000
            + data["hard"] * 1500
            + data["expert"] * 2000
            + data["general"] * 2000
        )

        missions_ws.write_row(
            f"A{str(i)}",
            [
                f"{user.alias} ({user.user_id})",
                data["easy"],
                data["medium"],
                data["hard"],
                data["expert"],
                data["general"],
                missions_total,
                ceil(data["xp"]),
                ceil(data["ta_cur_avg"]),
                ceil(data["mc_cur_avg"]),
                ceil(data["hc_cur_avg"]),
                ceil(data["bo_cur_avg"]),
            ],
        )
    missions_ws.set_column(1, 5, cell_format=center_fmt)

    # fmt: off
    column_map = {
        "ta": (0,  1,  2, 0),
        "mc": (4,  5,  6, 1),
        "hc": (8,  9,  10, 2),
        "bo": (12, 13, 14, 3),
    }
    ws_map = {
        "Unranked": (unranked_ws, 0),
        "Gold": (gold_ws, 1),
        "Diamond": (diamond_ws, 2),
        "Grandmaster": (grandmaster_ws, 3),
    }
    row_tracker = [
        # T  M  H  B
        [2, 2, 2, 2],  # Unranked
        [2, 2, 2, 2],  # Gold
        [2, 2, 2, 2],  # Diamond
        [2, 2, 2, 2],  # Grandmaster
    ]
    # fmt: on
    for category in ["ta", "mc", "hc", "bo"]:
        data: TournamentData = getattr(tournament, category, None)
        if not data:
            continue
        records = sorted(data.records, key=operator.attrgetter("record"))

        for record in records:
            user = await ExperiencePoints.find_user(record.user_id)
            user_cat_xp = tournament.xp[user.user_id][category]
            rank = user.rank
            rank = getattr(rank, category)
            worksheet, tracker_x = ws_map[rank]
            tracker_y = column_map[category][3]

            worksheet.write(
                row_tracker[tracker_x][tracker_y],
                column_map[category][0],
                f"{user.alias} ({user.user_id})",
            )
            worksheet.write(
                row_tracker[tracker_x][tracker_y],
                column_map[category][1],
                record.record,
            )
            worksheet.write(
                row_tracker[tracker_x][tracker_y],
                column_map[category][2],
                ceil(user_cat_xp),
            )

            row_tracker[tracker_x][tracker_y] += 1
    workbook.close()
