import os
from dminutes import miscUtils
reload(miscUtils)

from datetime import datetime
assetDirS = os.environ["ZOMB_ASSET_PATH"]

def releaseDateCompare(assetType = "prp", myFilter = "")

    assetDirS = os.environ["ZOMB_ASSET_PATH"]
    assetDirS = miscUtils.pathJoin(assetDirS,assetType)
    allAssetL = os.listdir(prpDirS)
    allAssetL.sort()

    for each in allPrpL:
        if not ".prp" in each and each != "prp_devTest_default":
            refAnimFileS = each+"_animRef.mb"
            refAnimFilePathS = miscUtils.pathJoin(prpDirS,each,'ref',refAnimFileS)
            refRenderFileS = each+"_renderRef.mb"
            refRenderFilePathS = miscUtils.pathJoin(prpDirS,each,'ref',refRenderFileS)

            modelingFileS = each+"_modeling.ma"
            modelingFilePathS = miscUtils.pathJoin(prpDirS,each,modelingFileS)
            animFileS = each+"_anim.ma"
            animFilePathS = miscUtils.pathJoin(prpDirS,each,animFileS)
            renderFileS = each+"_render.ma"
            renderFilePathS = miscUtils.pathJoin(prpDirS,each,renderFileS)
            
            dateAnimRefS =   "................"
            if os.path.isfile(refAnimFilePathS):
                statInfo = os.stat(refAnimFilePathS)
                statDate = statInfo.st_mtime
                statSize = statInfo.st_size
                if statSize > 75000:
                    dateAnimRefS = datetime.fromtimestamp(int(statDate)).strftime(u"%Y-%m-%d %H:%M")
                    
            dateRenderRefS = "................"    
            if os.path.isfile(refRenderFilePathS):
                statInfo = os.stat(refRenderFilePathS)
                statDate = statInfo.st_mtime
                statSize = statInfo.st_size
                if statSize > 75000:
                    dateRenderRefS = datetime.fromtimestamp(int(statDate)).strftime(u"%Y-%m-%d %H:%M")

            dateModelingS = "................"
            if os.path.isfile(modelingFilePathS):
                statInfo = os.stat(modelingFilePathS)
                statDate = statInfo.st_mtime
                statSize = statInfo.st_size
                if statSize > 75000:
                    dateModelingS = datetime.fromtimestamp(int(statDate)).strftime(u"%Y-%m-%d %H:%M")

            dateAnimS = "................"
            if os.path.isfile(animFilePathS):
                statInfo = os.stat(animFilePathS)
                statDateAnim = statInfo.st_mtime
                statSize = statInfo.st_size
                if statSize > 75000:
                    dateAnimS = datetime.fromtimestamp(int(statDate)).strftime(u"%Y-%m-%d %H:%M")
                    animFileL.append(each)

            dateRenderS = "................"
            if os.path.isfile(renderFilePathS):
                statInfo = os.stat(renderFilePathS)
                statDate = statInfo.st_mtime
                statSize = statInfo.st_size
                if statSize > 75000:
                    dateRenderS = datetime.fromtimestamp(int(statDate)).strftime(u"%Y-%m-%d %H:%M")               

            if myFilter = "":
                print "{:^48} modeling: {}    anim: {}    animRef: {}    render: {}    renderRef: {}".format(each, dateModelingS, dateAnimS, dateAnimRefS, dateRenderS, dateRenderRefS)
