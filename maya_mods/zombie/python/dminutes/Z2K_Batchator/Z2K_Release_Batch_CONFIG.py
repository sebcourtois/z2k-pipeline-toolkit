# Debug path variables
DEBUGFILE_PREVIZ_CHR='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_CHR_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_PRP_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='Z:/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_SET_Release_debug.txt'
DEBUGFILE= DEBUGFILE_PREVIZ_PRP

# GUI
Z2K_ICONPATH = "zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/"


# donner ici la list des assets du meme type to release
failedL=['prp_grandeRoue_default' ,'vhl_trainMine_default' ,'prp_tige_barbaPapa' ,'prp_boiteStickers_default',]
BATCH_ASSET_LIST =[
'vhl_voitureAurelien_default' ,
'prp_casquette_zombillenium' ,
'prp_paquetChewingGum_default' ,
'prp_caisseBandouliere_goodiesZ2k' ,
'prp_barbaPapa_default' ,
'prp_porteCle_crabe' ,
'prp_calepin_default' ,
'prp_balaisBallons_default' ,
'prp_balai_default',
'prp_gomme_default',
]

# Batch parameters - All configuration is Done Here.
ASSETCAT = "prp" #"chr","set","prp"
SOURCE_ASSET_TYPE="previz_scene"
DESTINATION_ASSET_TYPE= "previz_ref"
SGTASK= "Rig_Previz" # wip not in use "Rig Auto"
THECOMMENT= "Auto_Release_rockTheCasbah" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 0
PUBLISHMAYAFILE= 0
RELEASEMAYAFILE=1
UNLOCKFILE= 1
PREPUBLISH_PYSCRIPTL = [
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
]
PRERELEASE_PYSCRIPTL=[
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Previz_prp_check_batch.py",
]
