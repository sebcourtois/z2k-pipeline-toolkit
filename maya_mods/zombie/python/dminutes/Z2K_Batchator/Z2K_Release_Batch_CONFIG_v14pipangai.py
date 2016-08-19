#import os
#from dminutes import miscUtils
#reload(miscUtils)

#from datetime import datetime


# Debug path variables
DEBUGFILE_PREVIZ_CHR='C:/JIPE_DEV/debug_batch_files/Previz_CHR_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='C:/JIPE_DEV/debug_batch_files/Previz_PRP_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='C:/JIPE_DEV/debug_batch_files/Previz_SET_Release_debug.txt'


DEBUGFILE= 'C:/JIPE_DEV/debug_batch_files/Result_Release_debug.txt'

# GUI
Z2K_ICONPATH = "C:/JIPE_DEV/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/"




#assetDirS = os.environ["ZOMB_ASSET_PATH"]
#prpDirS = miscUtils.pathJoin(assetDirS,"env")
#allPrpL = os.listdir(prpDirS)
#allPrpL.sort()
#myPrpL = []

#animFileL=[]


BATCH_ASSET_LIST= [

"chr_ado18aine_groupie",
"chr_ado18aine_vamp",
"chr_ado_filleA",
"chr_ado_filleB",
"chr_ado_garsA",
"chr_ado_garsB",
"chr_dick_vampA",
"chr_dick_vampB",
"chr_dick_vampBatterie",
"chr_femmeFaty_default",
"chr_femmeFaty_fantome",
"chr_femmeFaty_visiteurA",
"chr_femmeFaty_visiteurB",
"chr_gamin1_visiteurA",
"chr_gamin1_visiteurB",
"chr_gamin3_default",
"chr_gamine_default",
"chr_gamine_lunettes",
"chr_gamine_noire",
"chr_gamine_visiteurE",
"chr_golem_default",
"chr_golem_peinture",
"chr_homme60aine_default",
"chr_homme60aine_fantome",
"chr_homme60aine_policier",
"chr_homme60aine_visiteurA",
"chr_homme60aine_visiteurB",
"chr_hommeSkinny_default",
"chr_hommeSkinny_moustache",
"chr_hommeSkinny_teteB",
"chr_zombie1_bras",
"chr_zombie1_cheveuxB",
"chr_zombie1_default",
"chr_zombie1_figC",
"chr_zombie1_figD",
"chr_zombie1_figE",
"chr_zombie1_jambes",
"chr_zombie1_sombre",
"chr_zombie1_versionB",
"chr_zombie1_visageCheveux",
"chr_zombie1_visageCheveuxB",




]

# donner ici la list des assets du meme type to release
#BATCH_ASSET_LIST = BATCH_ASSET_LIST

# Batch parameters - All configuration is Done Here.
ASSETCAT = "chr" #"chr","set","prp","vhl","c2d","env","fxp
SOURCE_ASSET_TYPE="anim_scene" #master_scene
DESTINATION_ASSET_TYPE= "anim_ref"
SGTASK= "Rig_Anim" # wip not in use "Rig Auto" or ""
SGVERSIONDATA={"sg_status_list":"fin"}#rev=Pending Review
THECOMMENT= "Auto_Release_rockTheCasbah !" #,"First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 1
PUBLISHMAYAFILE= 0
RELEASEMAYAFILE= 1
FORCERELEASE = 0
UNLOCKFILE= 1





PREPUBLISH_PYSCRIPTL = []


PRERELEASE_PYSCRIPTL=[
"C:/JIPE_DEV/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Anim_check_batch.py",
]



