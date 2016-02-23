import os
from dminutes import miscUtils
reload(miscUtils)

# Debug path variables
DEBUGFILE_PREVIZ_CHR='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_CHR_Release_debug.txt'
DEBUGFILE_PREVIZ_PRP='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_PRP_Release_debug.txt'
DEBUGFILE_PREVIZ_SET='//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Previz_SET_Release_debug.txt'

DEBUGFILE= '//zombiwalk/Z2K/06_PARTAGE/DEBUG_FILES/BATCHATOR/Result_Release_debug.txt'

# GUI
Z2K_ICONPATH = "zombie/python/dminutes/Z2K_ReleaseTool/icons/Z2K_ReleaseTool/"

TESTLIST= [
"set_devTest_default",
]


assetDirS = os.environ["ZOMB_ASSET_PATH"]
setDirS = miscUtils.pathJoin(assetDirS,"set")
allSetL = os.listdir(setDirS)
mySetL = []

for each in allSetL:
    if not "Bank" in each and not ".set" in each:
        mySetL.append(each)

omitL = ["set_devTest_default","set_quartierLac_vampirama","set_grandHuit_default","set_merNuages_default","set_littleTransylvania_entree", "set_rueVueDortoirs_default", 
"set_tablesPicNic_vampirama","set_pelouseSortieZombies_default"]

notReadyL=["set_nuagesRide_default", "set_discothequeInt_default","set_nuagesVortex_default",'set_conduitAeration_default']

setsDoneL = ["set_barInt_default","set_ruePrincipaleVillage_default",
"set_lotissementBarOuest_default","set_campagneZ2k_default",
"set_campagneVueParc_default", "set_campagneVueVillage_default","set_routeParcVillage_default","set_lotissementSortieVillage_default",
"set_quartierTrainMine_default","set_lotissementBarEst_default","set_lotissementPensionOuest_default", "set_cimetiere_default", 
"set_barExt_default", "set_entreeVillage_default","set_trainMineExt_default","set_grandeRoue_default","set_couloirs_staff",
"set_quartierGrandeRoue_vampirama","set_salleSyndic_default","set_pensionClasse_default","set_pensionExt_default","set_eglise_default",
"set_vestiaires_default","set_cageAscenseur_dortoirsZombies","set_chambreAurelien_default","set_dortoirsZombies_default","set_tours_default",
"set_quartierGrandeRoue_default","set_mainStreet_vampirama","set_trainMineHall_default","set_cageAscenseur_sdm",
"set_cageAscenseur_dortoirsZombiesPass","set_lotissementBarNord_default", "set_lotissementPensionEst_default", "set_parcLowdefGlobal_default",
"set_parcStreets_vampiramaTrous","set_trainMineExt_vampirama","set_trainMineHall_default","set_parcStreets_default"]


clareRequestL = ["set_salleSyndic_default","set_cimetiere_default","set_pensionClasse_default","set_pensionExt_default",
"set_eglise_default","set_lotissementBarEst_default","set_lotissementPensionEst_default","set_vestiaires_default","set_cageAscenseur_dortoirsZombies",
"set_chambreAurelien_default","set_dortoirsZombies_default","set_trainMineExt_default","set_tours_default","set_quartierTrainMine_default","set_bureauFrancis_default",
"set_staffParking_default","set_parcLowdefGlobal_default","set_grandeRoue_default","set_cageAscenseur_dortoirsZombiesPass","set_conduitAscenseur_dortoirsZombies",
"set_routePylones_default","set_entreeVillage_default","set_rueEntreeVillage_default","set_lotissementPensionOuest_default",
"set_lotissementBarNord_default","set_lotissementBarSud_default","set_salleMachines_default"]


setsErrorL = ["set_parcStreets_vampirama"]

#set_trainMineExt_default, set_parcStreets_vampirama, 
       
BATCH_ASSET_LIST = list(set(mySetL)-set(omitL)-set(notReadyL)-set(setsDoneL)-set(setsErrorL))
#BATCH_ASSET_LIST = clareRequestL

# donner ici la list des assets du meme type to release
# BATCH_ASSET_LIST =[
# "set_salleSyndic_default",
# ]

# Batch parameters - All configuration is Done Here.
ASSETCAT = "set" #"chr","set","prp","vhl","c2d","env","fxp
SOURCE_ASSET_TYPE="previz_scene"
DESTINATION_ASSET_TYPE= "previz_ref"
SGTASK= "Rig_Previz" # wip not in use "Rig Auto" or ""
SGVERSIONDATA={"sg_status_list":"rev"}#rev=Pending Review
THECOMMENT= "BATCH: re-rigged and cleaned" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 0
PUBLISHMAYAFILE= 1
RELEASEMAYAFILE=1
FORCERELEASE = 0
UNLOCKFILE= 1

PREPUBLISH_PYSCRIPTL = [
"C:/Users/abeermond/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Previz_set_rigAndClean.py",
"C:/Users/abeermond/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
]

# PREPUBLISH_PYSCRIPTL = [
# "C:/Users/abeermond/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
# ]

PRERELEASE_PYSCRIPTL=[
"C:/Users/abeermond/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Aladin_check_batch.py",
]
