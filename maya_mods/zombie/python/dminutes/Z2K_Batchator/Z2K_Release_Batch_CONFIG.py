# Debug path variables
DEBUGFILE_PREVIZ_CHR='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_CHR_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_PRP_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_SET_Release_debug.txt'
DEBUGFILE= DEBUGFILE_PREVIZ_PRP

# GUI
Z2K_ICONPATH = "zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/"


# donner ici la list des assets du meme type to release
BATCH_ASSET_LIST = ["prp_feuille_dessinMonstreLucie",
"prp_feuilleFroissee_dessinTombe",
"prp_feuilleFroissee_dessinTombe",
"prp_badgeMultiPass_gretchen",
"prp_balaisBallons_default",

"prp_carteControleur_aurelien",
"prp_cartes_jeu1",

"prp_casquette_zombillenium",
"prp_feuilles_miranda",
"prp_gomme_default",
"prp_grpSacs_souvenirZ2k",
"prp_hache_default",
"prp_limeOngle_default",

"prp_parapluie_default",
"prp_petalesRose_noire",
"prp_rose_noire",
"prp_stickChauvSou_mauve",
"prp_storeBaguette_default",
"prp_ticketZ2k_default",
"prp_cercueil_casse",
"prp_cercueil_default",]

# Batch parameters - All configuration is Done Here.
ASSETCAT = "prp" #"chr","set","prp"
SOURCE_ASSET_TYPE="previz_scene"
DESTINATION_ASSET_TYPE= "previz_ref"
SGTASK= "Rig_Previz" # wip not in use "Rig Auto"
THECOMMENT= "Auto_Release_rockTheCasbah" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 0
PUBLISHMAYAFILE= 0
RELEASEMAYAFILE= 0
UNLOCKFILE= 1
PREPUBLISH_PYSCRIPTL = [
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
]
PRERELEASE_PYSCRIPTL=[
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Previz_prp_check_batch.py",
]
