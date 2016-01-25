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
'chr_aurelien_polo',
'chr_barman_default',
'chr_sylvain_default',
'chr_maitresse_default',
'chr_gamin1_afro',
'chr_gamin1_default',
'chr_gamin1_roux',
'chr_gamin1_visiteurA',
'chr_gamin1_visiteurB',
'chr_gamin2_brun',
'chr_gamin2_cheveux',
'chr_gamin2_cheveuxTshirt',
'chr_gamin2_default',
'chr_gamin2_visiteurC',
'chr_gamin3_default',
'chr_gamin3_visiteurD',
'chr_penelope_blonde',
'chr_penelope_default',
'chr_penelope_gamineB',
'chr_penelope_visiteurF',
'chr_zombie1_bras',
'chr_zombie1_cheveuxB',
'chr_zombie1_default',
'chr_zombie1_figC',
'chr_zombie1_figD',
'chr_zombie1_figE',
'chr_zombie1_jambes',
'chr_zombie1_sombre',
'chr_zombie1_versionB',
'chr_zombie1_visageCheveux',
'chr_zombie1_visageCheveuxB',
'chr_jose_costume',
'chr_jose_coupe',
'chr_jose_default',
'chr_jose_figA',
'chr_jose_figB',
'chr_gamine_couette',
'chr_gamine_default',
'chr_gamine_lunettes',
'chr_gamine_noire',
'chr_gamine_visiteurE',
]

# Batch parameters - All configuration is Done Here.
ASSETCAT = "chr" #"chr","set","prp","vhl","c2d","env","fxp
SOURCE_ASSET_TYPE="anim_scene"
DESTINATION_ASSET_TYPE= "anim_ref"
SGTASK= "" # wip not in use "Rig Auto" or ""
THECOMMENT= "Auto_Release_rockTheCasbah" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 1
PUBLISHMAYAFILE= 0
RELEASEMAYAFILE=1
UNLOCKFILE= 1
PREPUBLISH_PYSCRIPTL = [
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
]
PRERELEASE_PYSCRIPTL=[
"C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Aladin_check_batch.py",
]
