# Debug path variables
DEBUGFILE_PREVIZ_CHR='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_CHR_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_PRP_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_SET_Release_debug.txt'
DEBUGFILE= '//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_Result_Release_debug.txt'

# GUI
Z2K_ICONPATH = "zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/"

TESTLIST= [
"chr_devTeam_testing",
"chr_testSeb_default",
"set_devTest_default",
]





# donner ici la list des assets du meme type to release
BATCH_ASSET_LIST =[
"set_devTest_default",

]

# Batch parameters - All configuration is Done Here.
ASSETCAT = "set" #"chr","set","prp","vhl","c2d","env","fxp
SOURCE_ASSET_TYPE="previz_scene"
DESTINATION_ASSET_TYPE= "previz_ref"
SGTASK= "Rig_Previz" # wip not in use "Rig Auto" or ""
THECOMMENT= "Auto_Release_rockTheCasbah" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 1
PUBLISHMAYAFILE= 0
RELEASEMAYAFILE=1
UNLOCKFILE= 0
PREPUBLISH_PYSCRIPTL = [
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
]
PRERELEASE_PYSCRIPTL=[
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Previz_aladin_check_batch.py",
]
