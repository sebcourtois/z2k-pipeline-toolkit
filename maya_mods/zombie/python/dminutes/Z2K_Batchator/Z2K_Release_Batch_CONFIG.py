
DEBUGFILE_PREVIZ_CHR='C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/debug/Previz_Chr_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/debug/Previz_Prp_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/debug/Previz_Set_Release_debug.txt'






DEBUGFILE_PREVIZ_CHR='C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/debug/Previz_Chr_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/debug/Previz_Prp_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/debug/Previz_Set_Release_debug.txt'





# don't forget the final "/" and put them all in the right direction : "/"
BATCH_SOURCEFOLDER = "Z:/06_PARTAGE/jp/RELEASE_PUBLISH/A_PUBLIER/2015_10_19/chr/"


# Batch parameters - All configuration is Done Here.
ASSETCAT = "chr" #"chr","set","prp"

SOURCE_ASSET_TYPE="previz_scene"
DESTINATION_ASSET_TYPE= "previz_ref"
SGTASK = "Rig_Previz" # wip not in use "Rig Auto"
THECOMMENT= "Auto_Release_rockTheCasbah" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA=1 
READONLY=0
PUBLISHMAYAFILE=0
RELEASEMAYAFILE =0 
UNLOCKFILE = 1
DEBUGFILE = DEBUGFILE_PREVIZ_CHR

PREPUBLISH_PYSCRIPTL = [
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/replaceAsset_batch_v001.py",
]

PRERELEASE_PYSCRIPTL=[
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Chr_previz_check_batch.py",
]

