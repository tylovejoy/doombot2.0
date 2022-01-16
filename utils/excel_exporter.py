import operator
from logging import getLogger

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
        merge_format = workbook.add_format({"align": "center", "bg_color": "#93c47d"})
        worksheet.merge_range("A1:C1", "Time Attack", merge_format)
        merge_format = workbook.add_format({"align": "center", "bg_color": "#ff9900"})
        worksheet.merge_range("D1:F1", "Mildcore", merge_format)
        merge_format = workbook.add_format({"align": "center", "bg_color": "#ff0000"})
        worksheet.merge_range("G1:I1", "Hardcore", merge_format)
        merge_format = workbook.add_format({"align": "center", "bg_color": "#ffff00"})
        worksheet.merge_range("J1:L1", "Bonus", merge_format)
        # Name, Time, Points titles
        worksheet.write_row("A2", ["Name", "Time", "Points"] * 4)

    # Format missions worksheet
    missions_ws.write_row(
        "A" + str(1),
        [
            "Names",
            "Easy",
            "Medium",
            "Hard",
            "Expert",
            "General",
            "Missions Total",
            "Total XP",
            "Average XP",
        ],
    )
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
            "A" + str(i),
            [
                user.alias,
                data["easy"],
                data["medium"],
                data["hard"],
                data["expert"],
                data["general"],
                missions_total,
                data["xp"],
                data["cur_avg"],
            ],
        )

    # fmt: off
    column_map = {
        "ta": (0,  1,  2, 0),
        "mc": (3,  4,  5, 1),
        "hc": (6,  7,  8, 2),
        "bo": (9, 10, 11, 3),
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
            user = await ExperiencePoints.find_user(record.posted_by)
            user_cat_xp = tournament.xp[user.user_id][category]
            rank = user.rank
            rank = getattr(rank, category)
            worksheet, tracker_x = ws_map[rank]
            tracker_y = column_map[category][3]

            worksheet.write(
                row_tracker[tracker_x][tracker_y], column_map[category][0], user.alias
            )
            worksheet.write(
                row_tracker[tracker_x][tracker_y],
                column_map[category][1],
                record.record,
            )
            worksheet.write(
                row_tracker[tracker_x][tracker_y], column_map[category][2], user_cat_xp
            )

            row_tracker[tracker_x][tracker_y] += 1
    workbook.close()
