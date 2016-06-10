import os
from dminutes import miscUtils
reload(miscUtils)

from datetime import datetime


# Debug path variables
DEBUGFILE_PREVIZ_CHR='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_CHR_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_PRP_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_SET_Release_debug.txt'

DEBUGFILE= '//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Result_Release_debug.txt'

# GUI
Z2K_ICONPATH = "zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/"




assetDirS = os.environ["ZOMB_ASSET_PATH"]
prpDirS = miscUtils.pathJoin(assetDirS,"env")
allPrpL = os.listdir(prpDirS)
allPrpL.sort()
myPrpL = []

animFileL=[]

myC2d=[
"env_parcZ2k_sq0040sh0010a",
"env_parcZ2k_sq0040sh0030a",
"env_village_sq0040sh0060a",
"env_parcZ2k_sq0040sh0080a",
"env_parcZ2k_sq0040sh0130a",
"env_tunnelEntreeHall_sq0050sh0100a",
"env_tunnelSortieHall_sq0050sh0120a",
"env_bgParcZ2k_sq0160sh0020a",
"env_bgParcZ2k_sq0160sh0090a",
"env_bgParcZ2k_sq0160sh0120a",
"env_bgParcZ2k_sq0160sh0130a",
"env_bgParcZ2k_sq0160sh0150a",
"env_rueParcZ2k_sq0160sh0160a",
"env_bgParcZ2k_sq0160sh0170a",
"env_bgParcZ2k_sq0180sh0010a",
"env_bgParcZ2k_sq0180sh0020a",
"env_bgParcZ2k_sq0180sh0040a",
"env_bgParcZ2k_sq0180sh0130a",
"env_refletParcZ2KAnim_sq0300sh0070a",
"env_parcZ2K34Plonge_sq0330sh0470a",
"env_parkZ2K_sq0330sh0600a",
"env_parcZ2kLP_sq0330sh0850a",
"env_refletServeurAnim_sq0350sh0010a",
"env_refletLune_sq0350sh0010a",
"env_parcZ2k_sq0350sh0030a",
"env_parcZ2k_sq0350sh0060a",
"env_parcZ2k_sq0350sh0090a",
"env_parcZ2k_sq0350sh0100a",
"env_parcZ2k_sq0350sh0120a",
"env_parcZ2k_sq0250sh0130a",
"env_parcZ2k_sq0360sh0020a",
"env_parcZ2k_sq0360sh0030a",
"env_parcZ2k_sq0360sh0060a",
"env_campagneVueVillage_sq0410sh0020",
"env_parcZ2kPlonge_sq0410sh0130",
"env_campagnePlonge_sq0410sh0150",
"env_campagnePlonge_sq0410sh0160",
"env_parcZ2kPlonge_sq0410sh0170",
"env_campagneVueVillage_sq0410sh0220",
"env_parcZ2k_sq0460sh0020a",
"env_parcZ2k_sq0480sh0260a",
"env_parcZ2k_sq0490sh0110a",
"env_parcZ2KCampagne_sq0500sh0080a",
"env_parcZ2KCampagne_sq0500sh0090a",
"env_parcZ2k_sq0510sh0078",
"env_salleMachinesCoupe_sq0535sh0130",
"env_parcZ2k_sq0580sh0030a",
"env_parcZ2k_sq0580sh0100a",
"env_parcZ2k_sq0640sh0050a",
"env_parcZ2k_sq0650sh0010a",
"env_parcZ2k_sq0680sh0130a",
"env_parcZ2k_sq0680sh0060a",
"env_trainMineHall_sortieVamp",
"env_trainMineHall_entreeVamp",
"env_parcZ2k_sq0700sh0090a",
"env_parcZ2k_sq0710sh0010a",
"env_parcZ2k_sq0740sh0100a",
"env_parcZ2k_sq0740sh0140a",
"env_village_sq0790sh0030a",
]



# BATCH_ASSET_LIST= [
# "prp_affichesVampirama_lotBarSud",
# ]

# donner ici la list des assets du meme type to release
BATCH_ASSET_LIST = myC2d[1:-1]

# Batch parameters - All configuration is Done Here.
ASSETCAT = "env" #"chr","set","prp","vhl","c2d","env","fxp
SOURCE_ASSET_TYPE="master_scene"
DESTINATION_ASSET_TYPE= "anim_ref"
SGTASK= "Rig_Anim" # wip not in use "Rig Auto" or ""
SGVERSIONDATA={"sg_status_list":"rev"}#rev=Pending Review
THECOMMENT= "BATCH: generate empty file to avoid error message in anim scenes" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 0
PUBLISHMAYAFILE= 1
RELEASEMAYAFILE= 1
FORCERELEASE = 1
UNLOCKFILE= 1





PREPUBLISH_PYSCRIPTL = [
"C:/Users/abeermond/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
]


PRERELEASE_PYSCRIPTL=[
"C:/Users/abeermond/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Aladin_check_batch.py",
]



