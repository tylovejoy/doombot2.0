import sys
from logging import getLogger

logger = getLogger(__name__)

if len(sys.argv) > 1:
    logger.info("Using test constants.")
    ROLE_WHITELIST = [
        195542852518805504,  # TEST - Mod
        801645674617634886,  # TEST - Tester
    ]

    GUILD_ID = 195387617972322306

    NEWEST_MAPS_ID = 856602254769782835

    VERIFICATION_CHANNEL_ID = 811467249100652586
    SPR_RECORDS_ID = 801496775390527548
    NON_SPR_RECORDS_ID = 856513618091049020
    TOP_RECORDS_ID = 873412962981908500

    SUGGESTIONS_ID = 873727339035521054
    TOP_SUGGESTIONS_ID = 873727376884924498

    TOURNAMENT_CHAT_ID = 840432678606995486
    TOURNAMENT_RANKS_ID = 907763621667430481
    TOURNAMENT_ORG_ID = 839876053828370503
    TOURNAMENT_SUBMISSION_ID = 840408122181812225
    EXPORT_ID = 840582536879145050
    TOURNAMENT_INFO_ID = 840713352832745474

    # Tournament Roles
    ORG_ROLE_ID = 840440551098679296

    TA_ROLE_ID = 841339455285886976
    MC_ROLE_ID = 841339569705844756
    HC_ROLE_ID = 841339590421381150
    BONUS_ROLE_ID = 841339621391859723

    BRACKET_TOURNAMENT_ROLE_ID = 841370294068576258
    TRIFECTA_ROLE_ID = 841378440078819378

    TA_CHAMP = 873611635829387294
    MC_CHAMP = 873611735238582392
    HC_CHAMP = 873611775642304544

else:
    logger.info("Using production constants.")
    ROLE_WHITELIST = [
        699145313520320542,  # LIVE - Admin
        725198459627634689,  # LIVE - Mod
        758399333942558800,  # LIVE - Tourny Org
        808426677562114122,  # LIVE - Record Org
    ]

    GUILD_ID = 689587520496730129

    NEWEST_MAPS_ID = 856605387050188821

    VERIFICATION_CHANNEL_ID = 813768098191769640
    SPR_RECORDS_ID = 693673770086301737
    NON_SPR_RECORDS_ID = 860291006493491210
    TOP_RECORDS_ID = 873572468982435860

    SUGGESTIONS_ID = 874051154055684117
    TOP_SUGGESTIONS_ID = 874049565244948571

    TOURNAMENT_CHAT_ID = 698004781188382811
    TOURNAMENT_RANKS_ID = 805332885321023499
    TOURNAMENT_ORG_ID = 788128445640343603
    TOURNAMENT_SUBMISSION_ID = 698003925168816139
    EXPORT_ID = 840614462494081075
    TOURNAMENT_INFO_ID = 774436274542739467

    # Tournament Roles
    ORG_ROLE_ID = 758399333942558800

    TA_ROLE_ID = 814532908638404618
    MC_ROLE_ID = 814532865672478760
    HC_ROLE_ID = 814532947461013545
    BONUS_ROLE_ID = 839952576866025543

    TRIFECTA_ROLE_ID = 814533106244649030
    BRACKET_TOURNAMENT_ROLE_ID = 830425028839211028

    TA_CHAMP = 839953205881208932
    MC_CHAMP = 839953397255634944
    HC_CHAMP = 839952979016417300