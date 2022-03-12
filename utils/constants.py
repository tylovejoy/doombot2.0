import sys
from logging import getLogger

logger = getLogger(__name__)

# is_test = len(sys.argv) > 1
#
# if is_test:
#     logger.info("Using test constants.")
# else:
#     logger.info("Using production constants.")

ROLE_WHITELIST = (
    # [
    #     195542852518805504,  # TEST - Mod
    #     801645674617634886,  # TEST - Tester
    # ]
    # if is_test
    # else
    [
        699145313520320542,  # LIVE - Admin
        725198459627634689,  # LIVE - Mod
        758399333942558800,  # LIVE - Tourny Org
        808426677562114122,  # LIVE - Record Org
    ]
)

# fmt: off
#                            [ prod constants ]
BOT_ID                     = 801483463642841150
GUILD_ID                   = 689587520496730129

SERVER_ANNOUNCEMENTS       = 756967122092949524

MOVIE_ROLE                 = 903667495922180167
GAME_ROLE                  = 903667578549968896

NEWEST_MAPS_ID             = 856605387050188821
MAP_MAKER_ID               = 746167804121841744


# Records channels
VERIFICATION_CHANNEL_ID    = 813768098191769640
SPR_RECORDS_ID             = 693673770086301737
NON_SPR_RECORDS_ID         = 860291006493491210
TOP_RECORDS_ID             = 873572468982435860

# Suggestion channels
SUGGESTIONS_ID             = 874051154055684117
TOP_SUGGESTIONS_ID         = 874049565244948571

# Tournament channels
TOURNAMENT_CHAT_ID         = 698004781188382811
TOURNAMENT_RANKS_ID        = 805332885321023499
TOURNAMENT_ORG_ID          = 788128445640343603
TOURNAMENT_SUBMISSION_ID   = 698003925168816139
EXPORT_ID                  = 840614462494081075
TOURNAMENT_INFO_ID         = 774436274542739467
HALL_OF_FAME_ID            = 840614462494081075

# Tournament Roles
ORG_ROLE_ID                = 758399333942558800

TA_ROLE_ID                 = 814532908638404618
MC_ROLE_ID                 = 814532865672478760
HC_ROLE_ID                 = 814532947461013545
BONUS_ROLE_ID              = 839952576866025543

BRACKET_TOURNAMENT_ROLE_ID = 830425028839211028
TRIFECTA_ROLE_ID           = 814533106244649030

# Tournament champion roles
TA_CHAMP                   = 839953205881208932
MC_CHAMP                   = 839953397255634944
HC_CHAMP                   = 839952979016417300

ERROR_LOGS                 = 849878847310528523
# fmt: on


# [ test constants ]
# 808340225460928552 if is_test else
# 195387617972322306 if is_test else
# 941737024602378282 if is_test else
# 946454378137653282 if is_test else
# 946454413298520114 if is_test else
# 856602254769782835 if is_test else
# 932337184231522405 if is_test else
# 811467249100652586 if is_test else
# 801496775390527548 if is_test else
# 856513618091049020 if is_test else
# 873412962981908500 if is_test else
# 873727339035521054 if is_test else
# 873727376884924498 if is_test else
# 840432678606995486 if is_test else
# 907763621667430481 if is_test else
# 839876053828370503 if is_test else
# 840408122181812225 if is_test else
# 840582536879145050 if is_test else
# 840713352832745474 if is_test else
# 931959281845157978 if is_test else
# 840440551098679296 if is_test else
# 841339455285886976 if is_test else
# 841339569705844756 if is_test else
# 841339590421381150 if is_test else
# 841339621391859723 if is_test else
# 841370294068576258 if is_test else
# 841378440078819378 if is_test else
# 873611635829387294 if is_test else
# 873611735238582392 if is_test else
# 873611775642304544 if is_test else
