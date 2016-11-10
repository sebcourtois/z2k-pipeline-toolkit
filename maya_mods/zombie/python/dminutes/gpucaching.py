
import os
import os.path as osp
import subprocess
import ctypes

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin
from pytd.util.sysutils import inDevMode, toStr

from pytaya.core import modeling
from pytaya.core import rendering
from pytaya.util.sysutils import withSelectionRestored

from davos_maya.tool.general import infosFromScene, iterGeoGroups

from dminutes import maya_scene_operations as mop

reload(modeling)
reload(rendering)
reload(mop)


def notifyBatchEnd(func):
    def doIt(*args, **kwargs):

        if mc.about(batch=True):
            try:
                ret = func(*args, **kwargs)
            except:
                ctypes.windll.user32.MessageBoxA(0, 'EXPORT FAILED !', 'GPU CACHE', 0x10 | 0x0 | 0x1000)
                raise
            else:
                ctypes.windll.user32.MessageBoxA(0, 'EXPORT DONE !', 'GPU CACHE', 0x40 | 0x0 | 0x1000)
        else:
            ret = func(*args, **kwargs)

        return ret
    return doIt

@withSelectionRestored
def exportFromAssets(selected=False, namespaces=None, outputDir=""):

    scnInfos = infosFromScene()
    damShot = scnInfos.get("dam_entity")

    sGeoGrpList = tuple(iterGeoGroups(sl=selected, namespaces=namespaces))
    if not sGeoGrpList:
        sMsg = "No geo groups found{}".format(" from selection.")
        raise RuntimeError(sMsg)

    sShotCam = mop.getShotCamera(damShot.name, fail=True).name()

    if outputDir:
        sOutDirPath = outputDir
    else:
        sOutDirPath = mop.getMayaCacheDir(damShot).replace("\\", "/")
        if not osp.exists(sOutDirPath):
            os.makedirs(sOutDirPath)

    sSelList = list(s.replace(":grp_geo", ":asset") for s in sGeoGrpList)
    mc.select(sSelList + [sShotCam], r=True)
    curTime = mc.currentTime(q=True)
    mc.currentTime(101)
    mc.refresh()
    try:
        sFilePath = pm.exportSelected(pathJoin(sOutDirPath, "export_gpuCache_tmp.mb"),
                                      type="mayaBinary",
                                      preserveReferences=False,
                                      shader=True,
                                      channels=True,
                                      constraints=True,
                                      expressions=True,
                                      constructionHistory=True,
                                      force=True)
    finally:
        mc.currentTime(curTime)

    sPython27Path = r"C:\Python27\python.exe"
    sZ2kEnvScript = os.environ["Z2K_LAUNCH_SCRIPT"]
    sAppPath = osp.join(os.environ["MAYA_LOCATION"], "bin", "mayabatch.exe")

    timeRange = (pm.playbackOptions(q=True, animationStartTime=True),
                 pm.playbackOptions(q=True, animationEndTime=True))

#    timeRange = (pm.playbackOptions(q=True, minTime=True),
#                 pm.playbackOptions(q=True, maxTime=True))

    sPyCmd = "from dminutes import gpucaching;reload(gpucaching);"
    sPyCmd += "gpucaching._doExportGpuCaches('{}',{},{},'{}');".format(sOutDirPath,
                                                                    timeRange[0],
                                                                    timeRange[1],
                                                                    sShotCam)
    sMelCmd = "python(\"{}\"); quit -f;".format(sPyCmd)

    sCmdArgs = [sPython27Path,
                osp.normpath(sZ2kEnvScript),
                "launch", "--update", "0", "--renew", "1",
                osp.normpath(sAppPath),
                "-file", osp.normpath(sFilePath),
                "-command", sMelCmd, "-prompt"
                ]

    if inDevMode():
        print sMelCmd
        print sCmdArgs

    SW_MINIMIZE = 6
    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = SW_MINIMIZE

    subprocess.Popen(sCmdArgs, startupinfo=info)

    pm.displayInfo("GPU caches are being exported from another maya process...")

@withSelectionRestored
def importGpuCache(sAbcPath):

    statinfo = os.stat(sAbcPath)
    sBaseName, _ = osp.splitext(osp.basename(sAbcPath))

    sGpuGrp = "|shot|grp_gpuCache"
    if not mc.objExists(sGpuGrp):
        mc.createNode("transform", n="grp_gpuCache", parent="|shot", skipSelect=True)

    sGpuShape = mc.createNode("gpuCache", n=sBaseName + "Shape", skipSelect=True)
    mc.addAttr(sGpuShape, ln="cacheFileMtime", at="long", dv=0)
    mc.addAttr(sGpuShape, ln="cacheFileSize", at="long", dv=0)

    sGpuXfm = mc.listRelatives(sGpuShape, parent=True, path=True)[0]
    sGpuXfm = mc.parent(sGpuXfm, sGpuGrp)[0]
    sGpuShape = mc.listRelatives(sGpuXfm, c=True, path=True)[0]

    mc.setAttr(sGpuShape + ".cacheFileName", sAbcPath, type="string")
    mc.setAttr(sGpuShape + ".cacheGeomPath", "|", type="string")
    mc.setAttr(sGpuShape + ".cacheFileMtime", long(statinfo.st_mtime))
    mc.setAttr(sGpuShape + ".cacheFileSize", statinfo.st_size)

    return sGpuXfm, sGpuShape

@mop.withoutUndo
def toggleSelected():

    scnInfos = infosFromScene()
    damShot = scnInfos.get("dam_entity")

    sAbcDirPath = mop.getMayaCacheDir(damShot).replace("\\", "/")

    sToSelList = []

    sCurSelList = mc.ls(sl=True)

    for sGeoGrp in iterGeoGroups(sl=True):

        sGpuXfm = "gpu_" + sGeoGrp.replace(":", "_")
        sNmspc = sGeoGrp.rsplit("|", 1)[-1].rsplit(":", 1)[0]

        sAstGrp = sNmspc + ":asset"
        if not mc.getAttr(sAstGrp + ".visibility"):
            continue

        if not mc.objExists(sGpuXfm):
            sAbcPath = pathJoin(sAbcDirPath, sGpuXfm + ".abc")
            if not osp.isfile(sAbcPath):
                pm.displayInfo("No such file: '{}'.".format(sAbcPath))
                continue

            sGpuXfm, _ = importGpuCache(sAbcPath)

        mc.setAttr(sAstGrp + ".visibility", False)
        mc.setAttr(sGpuXfm + ".visibility", True)
        _refreshOne(sGpuXfm)

        if sGpuXfm in sCurSelList:
            mc.select(sGpuXfm, d=True)

        sToSelList.append(sGpuXfm)

    for sGpuShape in mc.ls(sl=True, dag=True, leaf=True, type="gpuCache"):

        sGpuXfm = mc.listRelatives(sGpuShape, parent=True, path=True)[0]
        if not mc.getAttr(sGpuXfm + ".visibility"):
            continue

        sNspc = sGpuShape.split("gpu_", 1)[-1].rsplit("_grp_geo", 1)[0]

        sAstGrp = sNspc + ":asset"
        if not mc.objExists(sAstGrp):
            continue

        mc.setAttr(sAstGrp + ".visibility", True)
        mc.setAttr(sGpuXfm + ".visibility", False)

        if sAstGrp in sCurSelList:
            mc.select(sAstGrp, d=True)

        sToSelList.append(sAstGrp)

    if sToSelList:
        mc.select(sToSelList, r=True)

def setAllCachesVisible(bShow):

    scnInfos = infosFromScene()
    damShot = scnInfos.get("dam_entity")

    sAbcDirPath = mop.getMayaCacheDir(damShot).replace("\\", "/")

    sToSelList = []

    for sGeoGrp in tuple(iterGeoGroups()):

        #print sGeoGrp

        sGpuXfm = "gpu_" + sGeoGrp.replace(":", "_")
        sNspc = sGeoGrp.rsplit("|", 1)[-1].rsplit(":", 1)[0]

        sAstGrp = sNspc + ":asset"

        bGpuXfmFound = mc.objExists(sGpuXfm)
        if bShow and not bGpuXfmFound:
            sAbcPath = pathJoin(sAbcDirPath, sGpuXfm + ".abc")
            if not osp.isfile(sAbcPath):
                pm.displayInfo("No such file: '{}'.".format(sAbcPath))
                continue

            sGpuXfm, _ = importGpuCache(sAbcPath)

        mc.setAttr(sAstGrp + ".visibility", not bShow)
        if bGpuXfmFound:
            mc.setAttr(sGpuXfm + ".visibility", bShow)
            if bShow:
                _refreshOne(sGpuXfm)

        if bShow:
            sToSelList.append(sGpuXfm)
        else:
            sToSelList.append(sAstGrp)

#    if sToSelList:
#        mc.select(sToSelList, r=True)

    return

def refreshGpuNodes(**kwargs):

    bSelected = kwargs.pop("selected", kwargs.pop("sl", False))

    sGpuCacheList = mc.ls(sl=bSelected, dag=True, type="gpuCache")
    if not sGpuCacheList:
        sMsg = "No GPU Cache found in selection.\n\nRefresh all GPU Caches ?"
        sConfirm = pm.confirmDialog(title='DO YOU WANT TO...',
                                    message=sMsg,
                                    button=['OK', 'Cancel'],
                                    icon="question")
        if sConfirm == 'OK':
            sGpuCacheList = mc.ls(type="gpuCache")

    if sGpuCacheList:
        for sGpuShape in sGpuCacheList:
            _refreshOne(sGpuShape)

def _refreshOne(sGpuNode, force=False):

    if mc.objectType(sGpuNode, isType="transform"):
        sGpuShape = mc.listRelatives(sGpuNode, c=True, type="gpuCache", path=True)[0]
    elif mc.objectType(sGpuNode, isType="gpuCache"):
        sGpuShape = sGpuNode
    else:
        raise TypeError("Not a gpuCache node: '{}'".format(sGpuNode))

    sAbcPath = mc.getAttr(sGpuShape + ".cacheFileName")
    if not sAbcPath:
        return

    try:
        statinfo = os.stat(sAbcPath)
    except OSError as e:
        pm.displayWarning(toStr(e))
        return

    if not force:
        t = mc.getAttr(sGpuShape + ".cacheFileMtime")
        s = mc.getAttr(sGpuShape + ".cacheFileSize")

        if (s == statinfo.st_size) and (t == long(statinfo.st_mtime)):
            pm.displayInfo("'{}' already up-to-date: No refresh needed.".format(sGpuShape))
            return

    pm.displayInfo("Refreshing '{}'...".format(sGpuShape))

    mc.gpuCache(sGpuShape, e=True, refresh=True)
    mc.setAttr(sGpuShape + ".cacheFileMtime", long(statinfo.st_mtime))
    mc.setAttr(sGpuShape + ".cacheFileSize", statinfo.st_size)

    return True

@notifyBatchEnd
def _doExportGpuCaches(sOutDirPath, startTime, endTime, sCamForBaking):

    if mc.about(batch=True):
        if mc.evaluationManager(q=True, mode=True) != "parallel":
            mc.evaluationManager(e=True, mode="parallel")
        mc.undoInfo(state=False)

    sGeoGrpList = mc.ls("*:grp_geo")
    if not sGeoGrpList:
        return

    for sGeoGrp in sGeoGrpList:

        sGeoMeshList = list(iterMeshesToExport(sGeoGrp))
        if not sGeoMeshList:
            continue

        sObjAttr = sGeoGrp + ".smoothLevel1"
        if mc.objExists(sObjAttr):
            mc.setAttr(sObjAttr, 0)

        sObjAttr = sGeoGrp + ".smoothLevel2"
        if mc.objExists(sObjAttr):
            if mc.getAttr(sObjAttr) > 1:
                mc.setAttr(sObjAttr, 1)

        modeling.bakeDiffuseToVertexColor(meshes=sGeoMeshList, ambient=0.0, camera=sCamForBaking)
        modeling.disableVertexColorDisplay(meshes=sGeoMeshList)

        oShaderList = rendering.shadersFromObjects(sGeoMeshList, connectedTo="surfaceShader")
        rendering.duplicateShadersPerObject(oShaderList)

        oShaderList = rendering.shadersFromObjects(sGeoMeshList, connectedTo="surfaceShader")
        rendering.averageVertexColorsToMaterial(oShaderList)
        mc.select(cl=True)

    try:
        sMelCmd = r'int $frame = frame;print ("frame: "+$frame+"\n");'
        sExprNode = mc.expression(s=sMelCmd, ae=True, uc="all")

        mc.gpuCache(sGeoGrpList, startTime=startTime, endTime=endTime,
                    optimize=True, optimizationThreshold=40000,
                    writeMaterials=True, dataFormat="ogawa",
                    #showStats=True, showFailed=True, showGlobalStats=True,
                    filePrefix="gpu_", clashOption="nodeName", directory=sOutDirPath)
    finally:
        mc.delete(sExprNode)

def iterMeshesToExport(sGeoGrp):

    for sMeshPath in mc.ls(sGeoGrp, dag=True, type="mesh", ni=True):

        sMeshName = sMeshPath.rsplit("|", 1)[-1].rsplit(":", 1)[-1].lower()

        if sMeshName.startswith("geo_outline"):
            hideXfm(sMeshPath)
            continue

        if not isMeshVisible(sMeshPath):
            continue

        if sMeshName.startswith("geo_"):
            yield sMeshPath
            continue

        hideXfm(sMeshPath)

def hideXfm(sShapePath):
    return mc.setAttr(mc.listRelatives(sShapePath, parent=True, path=True)[0] + ".visibility", False)

def isMeshVisible(sMeshPath):

    if not mc.getAttr(sMeshPath + ".visibility"):
        return False

    return mc.getAttr(mc.listRelatives(sMeshPath, parent=True, path=True)[0] + ".visibility")
