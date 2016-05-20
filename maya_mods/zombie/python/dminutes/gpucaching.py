
import os
import os.path as osp
import subprocess

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin
from pytd.util.sysutils import inDevMode, toStr

from pytaya.core import modeling
from pytaya.core import rendering
from pytaya.util.sysutils import withSelectionRestored

from davos_maya.tool.general import entityFromScene
from dminutes import maya_scene_operations as mop
from dminutes.geocaching import iterGeoGroups

reload(modeling)
reload(rendering)
reload(mop)


def hideXfm(sShapePath):
    return mc.setAttr(mc.listRelatives(sShapePath, parent=True, path=True)[0] + ".visibility", False)

def isMeshVisible(sMeshPath):

    if not mc.getAttr(sMeshPath + ".visibility"):
        return False

    return mc.getAttr(mc.listRelatives(sMeshPath, parent=True, path=True)[0] + ".visibility")

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

def _batchExport(sOutDirPath, startTime, endTime, bakeCamera):

    if (not inDevMode()) and (not mc.about(batch=True)):
        raise RuntimeError("Must be called in batch mode.")

    if mc.evaluationManager(q=True, mode=True) != "parallel":
        mc.evaluationManager(e=True, mode="parallel")

    mc.undoInfo(state=False)

    sGeoGrpList = mc.ls("*:grp_geo")
    if not sGeoGrpList:
        return

    for sGeoGrp in sGeoGrpList:

            mc.setAttr(sGeoGrp + ".smoothLevel1", 0)
            if mc.getAttr(sGeoGrp + ".smoothLevel2") > 1:
                mc.setAttr(sGeoGrp + ".smoothLevel2", 1)

            sGeoMeshList = list(iterMeshesToExport(sGeoGrp))

            modeling.bakeDiffuseToVertexColor(meshes=sGeoMeshList, ambient=0.0, camera=bakeCamera)
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

@withSelectionRestored
def importGpuCache(sBaseName):

    damShot = entityFromScene()
    sAbcDirPath = mop.getGeoCacheDir(damShot).replace("\\", "/")
    sAbcPath = pathJoin(sAbcDirPath, sBaseName + ".abc")

    if not osp.isfile(sAbcPath):
        pm.displayInfo("No GPU cache file: '{}'.".format(sAbcPath))
        return

    statinfo = os.stat(sAbcPath)

    sGpuGrp = "|shot|grp_gpuCache"
    if not mc.objExists(sGpuGrp):
        mc.createNode("transform", n="grp_gpuCache", parent="shot")

    sGpuShape = mc.createNode("gpuCache", n=sBaseName + "Shape")
    mc.addAttr(sGpuShape, ln="cacheFileMtime", at="long", dv=0)
    mc.addAttr(sGpuShape, ln="cacheFileSize", at="long", dv=0)

    sGpuXfm = mc.listRelatives(sGpuShape, parent=True, path=True)[0]
    mc.rename(sGpuXfm, sBaseName)
    mc.parent(sGpuXfm, sGpuGrp)

    mc.setAttr(sGpuShape + ".cacheFileName", sAbcPath, type="string")
    mc.setAttr(sGpuShape + ".cacheGeomPath", "|", type="string")
    mc.setAttr(sGpuShape + ".cacheFileMtime", long(statinfo.st_mtime))
    mc.setAttr(sGpuShape + ".cacheFileSize", statinfo.st_size)

    return sGpuXfm, sGpuShape

@withSelectionRestored
def exportSelected():

    damShot = entityFromScene()

    sGeoGrpList = tuple(iterGeoGroups(sl=True))
    if not sGeoGrpList:
        raise RuntimeError("Selected assets has NO 'grp_geo' to export.")

    sShotCam = mop.getShotCamera(damShot.name, fail=True).name()

    sAbcDirPath = mop.getGeoCacheDir(damShot).replace("\\", "/")
    if not osp.exists(sAbcDirPath):
        os.makedirs(sAbcDirPath)

    sSelList = list(s.replace(":grp_geo", ":asset") for s in sGeoGrpList)
    mc.select(sSelList + [sShotCam], r=True)
    curTime = mc.currentTime(q=True)
    mc.currentTime(101)
    mc.refresh()
    try:
        sFilePath = pm.exportSelected(pathJoin(sAbcDirPath, "export_gpuCache_tmp.mb"),
                                      type="mayaAscii",
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
    sPyCmd += "gpucaching._batchExport('{}',{},{},'{}');".format(sAbcDirPath,
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

@mop.withoutUndo
def toggleSelected():

    sToSelList = []

    sCurSelList = mc.ls(sl=True)

    for sGeoGrp in iterGeoGroups(sl=True):

        sGpuXfm = "gpu_" + sGeoGrp.replace(":", "_")
        sNspc = sGeoGrp.rsplit("|", 1)[-1].rsplit(":", 1)[0]

        sAstGrp = sNspc + ":asset"
        if not mc.getAttr(sAstGrp + ".visibility"):
            continue

        if not mc.objExists(sGpuXfm):
            if not importGpuCache(sGpuXfm):
                continue

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

def setAllCacheVisible(bShow):

    sToSelList = []

    for sGeoGrp in tuple(iterGeoGroups()):

        print sGeoGrp

        sGpuXfm = "gpu_" + sGeoGrp.replace(":", "_")
        sNspc = sGeoGrp.rsplit("|", 1)[-1].rsplit(":", 1)[0]

        sAstGrp = sNspc + ":asset"

        bGpuXfmFound = mc.objExists(sGpuXfm)
        if bShow and not bGpuXfmFound:
            if not importGpuCache(sGpuXfm):
                continue

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

def _refreshOne(sGpuNode):

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

def refreshSelected():

    sGpuCacheList = mc.ls(sl=True, dag=True, type="gpuCache")
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

