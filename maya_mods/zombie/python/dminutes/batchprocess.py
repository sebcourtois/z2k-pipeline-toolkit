
import os.path as osp
import traceback
from pprint import pprint

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin

from davos.core.damproject import DamProject
from davos.core.utils import mkVersionSuffix

from pytaya.core import system as myasys

from davos_maya.tool import reference as myaref
from davos_maya.tool import general as myagen
from davos_maya.tool import publishing

from dminutes import geocaching
from dminutes import finalLayout
from dminutes import shotconformation as shotconfo

reload(geocaching)
reload(finalLayout)
reload(myaref)
reload(myagen)
reload(shotconfo)
reload(publishing)
reload(myasys)

def quitWithStatus(func):
    def doIt(*args, **kwargs):
        bSave = kwargs.pop("save", False)
        bQuit = kwargs.pop("quit", mc.about(batch=True))
        try:
            res = func(*args, **kwargs)
        except:
            if bQuit:
                sTrace = traceback.format_exc()
#                lines = [""] + sTrace.splitlines(True)
#                print "!ERROR!".join(lines)
                pm.displayError(sTrace)
                mc.quit(f=True, exitCode=1)
            else:
                raise
        else:
            if bSave:
                pm.saveFile(force=True)
            if bQuit:
                mc.quit(force=True, exitCode=0)
        return res
    return doIt

@quitWithStatus
def setupLayoutScene(**kwargs):

    proj = DamProject("zombillenium", user="rrender", password="arn0ld&r0yal", standalone=False)

    scnInfos = myagen.infosFromScene(project=proj)
    if scnInfos["resource"] != "layout_scene":
        pm.displayWarning("Not a layout scene: batchprocess.setupLayoutScene() not applied.")
        return

    def excludeRef(oFileRef):
        return(not oFileRef.namespace.lower().startswith("set_"))

    myaref.loadAssetsAsResource("anim_ref", checkSyncState=True, selected=False,
                                exclude=excludeRef, fail=True)

    sOutDirPath = pm.sceneName().dirname() + "/geoCache"
    mc.select("set_*:grp_geo")
    exportData = geocaching.exportCaches(selected=True, confirm=False,
                                         sceneInfos=scnInfos, outputDir=sOutDirPath)

    jobList = exportData["jobs"]
    for jobInfos in jobList:
        sFilePath = jobInfos["file"]
        if not osp.isabs(sFilePath):
            jobInfos["file"] = pathJoin(sOutDirPath, sFilePath)

    #pprint(exportData)

    myaref.loadAssetsAsResource("render_ref", checkSyncState=True, selected=False,
                                exclude=excludeRef, fail=True)

    geocaching.importCaches(jobs=jobList, layoutViz=False, useCacheSet=True,
                            dryRun=False, beforeHistory=False, removeRefs=True,
                            showScriptEditor=False, sceneInfos=scnInfos)

    finalLayout.renderSetup()

def buildRenderScene(sShotName, sSrcScnPath, publish=False, dryRun=False):

    proj = DamProject("zombillenium")
    damShot = proj.getShot(sShotName)
    shotLib = damShot.getLibrary()

    srcScn = proj.rcFileFromPath(sSrcScnPath, library=shotLib, dbNode=False)

    if publish:
        sComment = "built from " + srcScn.name.replace(damShot.name + "_", "")
        pubFile = damShot.getRcFile("public", "rendering_scene")

    if srcScn.isVersionFile():
        sVersSuffix = mkVersionSuffix(srcScn.versionFromName())
        headFile = srcScn.getHeadFile(dbNode=False)
        copiedFile = srcScn
    else:
        sVersSuffix = ""
        headFile = srcScn
        copiedFile = None

    sSuffix = "".join((sVersSuffix, "-toLighting"))
    privScn, _ = headFile.copyToPrivateSpace(suffix=sSuffix, existing="replace",
                                             sourceFile=copiedFile)
    srcScn = privScn
    sSrcScnPath = srcScn.absPath()

    myasys.openScene(sSrcScnPath, force=True, fail=False, lrd="none")

    relatAstList = myagen.listRelatedAssets(damShot)
    myaref.lockAssetRefsToRelatedVersion(relatAstList)

    if not pm.listReferences(loaded=True, unloaded=False):
        pm.saveFile(force=True)
        pm.openFile(sSrcScnPath, force=True, lrd="all")

    shotconfo.finalLayoutToLighting(gui=False)

    if not dryRun:
        pm.saveFile(force=True)

    if publish and (not dryRun):
        sgVersData = {"sg_status_list":"rdy"}
        _, sgVersion = pubFile.publishVersion(sSrcScnPath, autoLock=True,
                                              autoUnlock=True,
                                              comment=sComment,
                                              sgVersionData=sgVersData)
        if sgVersion:
            publishing.linkAssetVersionsInShotgun(damShot, sgVersion)

