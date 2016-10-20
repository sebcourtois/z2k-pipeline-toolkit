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


renderRefL=[]

assetDirS = os.environ["ZOMB_ASSET_PATH"]
prpDirS = miscUtils.pathJoin(assetDirS,"set")
allPrpL = os.listdir(prpDirS)
allPrpL.sort()
myPrpL = []

for each in allPrpL:
    if not ".set" in each and each != "prp_devTest_default":
        refAnimFileS = each+"_animRef.mb"
        refAnimFilePathS = miscUtils.pathJoin(prpDirS,each,'ref',refAnimFileS)
        refRenderFileS = each+"_renderRef.mb"
        refRenderFilePathS = miscUtils.pathJoin(prpDirS,each,'ref',refRenderFileS)


        renderFileS = each+"_master.ma"
        renderFilePathS = miscUtils.pathJoin(prpDirS,each,renderFileS)
        

        dateRenderRefS = "................"    
        if os.path.isfile(refRenderFilePathS):
            statInfo = os.stat(refRenderFilePathS)
            statDate = statInfo.st_mtime
            statSize = statInfo.st_size
            if statSize > 75000:
                dateRenderRefS = datetime.fromtimestamp(int(statDate)).strftime(u"%Y-%m-%d %H:%M")
                renderRefL.append(each)

        
print renderRefL


BATCH_ASSET_LIST = list(renderRefL)

#set_trainMineExt_default, set_parcStreets_vampirama, 
       
#BATCH_ASSET_LIST = list(set(mySetL)-set(omitL)-set(notReadyL)-set(setsDoneL)-set(setsErrorL))
#BATCH_ASSET_LIST = clareRequestL


# donner ici la list des assets du meme type to release
BATCH_ASSET_LIST = ["set_accueil13eme_default"]

# Batch parameters - All configuration is Done Here.
ASSETCAT = "set" #"chr","set","prp","vhl","c2d","env","fxp
SOURCE_ASSET_TYPE="master_scene" #"anim_scene", "previz_scene", "render_scene"
DESTINATION_ASSET_TYPE= "render_ref"
SGTASK= "Rig_Render" # wip not in use "Rig Auto" or ""
SGVERSIONDATA={"sg_status_list":"rev"}#rev=Pending Review
THECOMMENT= "BATCH: re-release to remove display layers" #"Auto_Release_rockTheCasbah !","First_publish_RockTheCasbah"
OPENINMAYA= 1 
READONLY= 1
PUBLISHMAYAFILE= 0
RELEASEMAYAFILE=1
FORCERELEASE = 0
UNLOCKFILE= 0





PREPUBLISH_PYSCRIPTL = [
"C:/Users/abeermond/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/testProject.py",
]


PRERELEASE_PYSCRIPTL=[
"C:/Users/abeermond/DEVSPACE/git/z2k-pipeline-toolkit/maya_mods/zombie/python/dminutes/Z2K_Batchator/scripts/Aladin_check_batch.py",
]