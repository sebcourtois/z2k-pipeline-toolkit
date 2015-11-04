# Debug path variables
DEBUGFILE_PREVIZ_CHR='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_CHAR_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_PROP_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_SET_Release_debug.txt'
DEBUGFILE= DEBUGFILE_PREVIZ_PRP

# GUI
Z2K_ICONPATH = "zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/"

# don't forget the final "/" and put them all in the right direction : "/"
BATCH_SOURCEFOLDER = "Z:/06_PARTAGE/jp/RELEASE_PUBLISH/A_PUBLIER/2015_10_26/ALL/"

# Batch parameters - All configuration is Done Here.
ASSETCAT = "prp" #"chr","set","prp"
SOURCE_ASSET_TYPE="previz_scene"
DESTINATION_ASSET_TYPE= "previz_ref"
SGTASK= "Rig_Previz" # wip not in use "Rig Auto"
THECOMMENT= "Auto_Release_rockTheCasbah" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 0
PUBLISHMAYAFILE= 1
RELEASEMAYAFILE= 1
UNLOCKFILE= 1
PREPUBLISH_PYSCRIPTL = [
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/replaceAsset_batch_v001.py",
]
PRERELEASE_PYSCRIPTL=[
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Previz_prp_check_batch.py",
]
