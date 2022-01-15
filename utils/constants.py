import sys
from logging import getLogger

logger = getLogger(__name__)

is_test = len(sys.argv) > 1

if is_test:
    logger.info("Using test constants.")
else:
    logger.info("Using production constants.")

ROLE_WHITELIST = (
    [
        195542852518805504,  # TEST - Mod
        801645674617634886,  # TEST - Tester
    ]
    if is_test
    else [
        699145313520320542,  # LIVE - Admin
        725198459627634689,  # LIVE - Mod
        758399333942558800,  # LIVE - Tourny Org
        808426677562114122,  # LIVE - Record Org
    ]
)

# fmt: off
#                            [ test constants ]                 [ prod constants ]
BOT_ID                     = 808340225460928552 if is_test else 801483463642841150
GUILD_ID                   = 195387617972322306 if is_test else 689587520496730129

NEWEST_MAPS_ID             = 856602254769782835 if is_test else 856605387050188821

# Records channels
VERIFICATION_CHANNEL_ID    = 811467249100652586 if is_test else 813768098191769640
SPR_RECORDS_ID             = 801496775390527548 if is_test else 693673770086301737
NON_SPR_RECORDS_ID         = 856513618091049020 if is_test else 860291006493491210
TOP_RECORDS_ID             = 873412962981908500 if is_test else 873572468982435860

# Suggestion channels
SUGGESTIONS_ID             = 873727339035521054 if is_test else 874051154055684117
TOP_SUGGESTIONS_ID         = 873727376884924498 if is_test else 874049565244948571

# Tournament channels
TOURNAMENT_CHAT_ID         = 840432678606995486 if is_test else 698004781188382811
TOURNAMENT_RANKS_ID        = 907763621667430481 if is_test else 805332885321023499
TOURNAMENT_ORG_ID          = 839876053828370503 if is_test else 788128445640343603
TOURNAMENT_SUBMISSION_ID   = 840408122181812225 if is_test else 698003925168816139
EXPORT_ID                  = 840582536879145050 if is_test else 840614462494081075
TOURNAMENT_INFO_ID         = 840713352832745474 if is_test else 774436274542739467
HALL_OF_FAME_ID            = 931959281845157978 if is_test else 0  # TODO: id

# Tournament Roles
ORG_ROLE_ID                = 840440551098679296 if is_test else 758399333942558800

TA_ROLE_ID                 = 841339455285886976 if is_test else 814532908638404618
MC_ROLE_ID                 = 841339569705844756 if is_test else 814532865672478760
HC_ROLE_ID                 = 841339590421381150 if is_test else 814532947461013545
BONUS_ROLE_ID              = 841339621391859723 if is_test else 839952576866025543

BRACKET_TOURNAMENT_ROLE_ID = 841370294068576258 if is_test else 830425028839211028
TRIFECTA_ROLE_ID           = 841378440078819378 if is_test else 814533106244649030

# Tournament champion roles
TA_CHAMP                   = 873611635829387294 if is_test else 839953205881208932
MC_CHAMP                   = 873611735238582392 if is_test else 839953397255634944
HC_CHAMP                   = 873611775642304544 if is_test else 839952979016417300
# fmt: on
