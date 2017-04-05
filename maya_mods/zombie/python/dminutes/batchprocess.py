
import os
import os.path as osp
import traceback
from pprint import pprint
import re

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin, pathNorm, pathEqual

from davos.core.damproject import DamProject
from davos.core.utils import mkVersionSuffix

from zomblib import damutils

from pytaya.core import system as myasys
from pytaya.core.cleaning import deleteAllJunkShapes
from pytaya.core.general import lsNodes

from davos_maya.tool import reference as myaref
from davos_maya.tool import general as myagen
from davos_maya.tool import publishing

from dminutes import geocaching
from dminutes import finalLayout
from dminutes import shotconformation as shotconfo
from dminutes import sceneManager
from dminutes import rendering

reload(geocaching)
reload(finalLayout)
reload(myaref)
reload(myagen)
reload(shotconfo)
reload(publishing)
reload(myasys)
reload(sceneManager)
reload(rendering)


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

    geocaching.importCaches(jobs=jobList, layout=True, useCacheSet=True,
                            dryRun=False, beforeHistory=False, removeRefs=True,
                            showScriptEditor=False, sceneInfos=scnInfos)

    finalLayout.renderSetup()

def buildRenderScene(sSrcScnPath, publish=False, dryRun=False):

    srcScnInfos = myagen.infosFromScene(sSrcScnPath)
    damShot = srcScnInfos["dam_entity"]
    srcScn = srcScnInfos["rc_entry"]
    if not srcScn.isVersionFile():
        raise ValueError("Source scene is NOT a version file: '{}'"
                         .format(sSrcScnPath))

    pubDstScn = damShot.getRcFile("public", "rendering_scene")
    sComment = "built from " + srcScn.name.replace(damShot.name + "_", "")
    sgVersData = {"sg_status_list":"rdy"}

    if publish:
        pubDstScn.ensureLocked(autoLock=True)

    try:
        privDstScn, _ = pubDstScn.copyToPrivateSpace(suffix=pubDstScn.makeEditSuffix(),
                                                     existing="replace",
                                                     sourceFile=srcScn)
        sSrcScnPath = privDstScn.absPath()

        myasys.openScene(sSrcScnPath, force=True, fail=False)
        mc.refresh()

        relatAstList = myagen.listRelatedAssets(damShot)
        myaref.lockAssetRefsToRelatedVersion(relatAstList)

        shotconfo.finalLayoutToLighting(gui=False)

        geocaching.conformAbcNodeNames()
        geocaching.exportLayoutInfo(publish=publish, dryRun=dryRun, sceneInfos=srcScnInfos)

        if publish:
            scnInfos = myagen.infosFromScene()
            scnMng = sceneManager.SceneManager(scnInfos)
            scnMng.publish(comment=sComment, sgVersionData=sgVersData, 
                           dryRun=dryRun, autoUnlock=False)
    finally:
        if publish:
            pubDstScn.setLocked(False)

def exportLayoutInfos(sSrcScnPath, publish=False, dryRun=False):

    scnInfos = myagen.infosFromScene(sSrcScnPath)
    #damShot = scnInfos["dam_entity"]

    myasys.openScene(sSrcScnPath, force=True, fail=False)
    mc.refresh()

    geocaching.conformAbcNodeNames()
    geocaching.exportLayoutInfo(publish=publish, dryRun=dryRun, sceneInfos=scnInfos)

def publishCfxCaches(sSrcScnPath, publish=False, dryRun=False):

#    raise RuntimeError("Bypassing job")

    from davos_maya.tool import dependency_scan;reload(dependency_scan)

    srcScnInfos = myagen.infosFromScene(sSrcScnPath)
    damShot = srcScnInfos["dam_entity"]
    srcScn = srcScnInfos["rc_entry"]
    bPublicSrc = srcScn.isPublic()
    if bPublicSrc and not srcScn.isVersionFile():
        raise ValueError("Source scene is NOT a version file: '{}'"
                         .format(sSrcScnPath))

    sCurUser = damShot.project.loggedUser().loginName

    pubDstScn = damShot.getRcFile("public", "charFx_scene")
    sComment = "BATCH: published caches 2"
    sgVersData = {"sg_status_list":"omt"}

    if publish:
        pubDstScn.ensureLocked(autoLock=True)

    try:
        if bPublicSrc:
            privDstScn, _ = pubDstScn.copyToPrivateSpace(suffix=pubDstScn.makeEditSuffix(),
                                                         existing="replace",
                                                         sourceFile=srcScn)
            sSrcScnPath = privDstScn.absPath()

        openKwargs = dict(force=True, fail=False)
#        if (not publish) and dryRun:
#            openKwargs.update(lrd="none")

        if not pathEqual(pm.sceneName(), sSrcScnPath):
            myasys.openScene(sSrcScnPath, **openKwargs)
            srcScnInfos = myagen.infosFromScene()

        deleteAllJunkShapes()

        dependDct = None
        sCacheNodeList = lsNodes(type="cacheFile", not_rn=True, nodeNames=True)
        if sCacheNodeList:

            if False:
                # grouping CFX meshes by assets to world
                sGeoGrpList = mc.ls("chr_*:grp_geo") + mc.ls("prp_*:grp_geo") + mc.ls("vhl_*:grp_geo")
                worldGrpDct = {}
                for sXfm in mc.ls(lsNodes(sGeoGrpList, dag=True, not_rn=True, nodeNames=True), exactType="transform"):
                    sParent = mc.listRelatives(sXfm, p=True, path=True)[0]
                    sAstNmspc = sParent.rsplit("|", 1)[-1].rsplit(":", 1)[0]
                    worldGrpDct.setdefault(sAstNmspc, []).append(sXfm)

                for sAstNmspc, sObjList in worldGrpDct.iteritems():
                    print u"grouping under '{}': {}".format(sAstNmspc + "_CFX", sObjList)
                    mc.group(sObjList, name=sAstNmspc + "_CFX", world=True)

            # filter useless nodes through preview of exported selection for chr, prp and vhl assets
            sNodeList = None
            if False:
                sToSelList = mc.ls("chr_*:asset") + mc.ls("prp_*:asset") + mc.ls("vhl_*:asset")
                if sToSelList:
                    mc.select(sToSelList)
                    sNodeList = mc.file(exportSelected=True, preview=True, force=True, type="mayaAscii",
                                        preserveReferences=True, shader=False, channels=True,
                                        constraints=True, expressions=True, constructionHistory=True)
                    print "Nodes to connected to an asset ref:", len(sNodeList)

            if sNodeList:
                sCacheNodeList = lsNodes(sNodeList, type="cacheFile", not_rn=True, nodeNames=True)

            if False:
                sCurUserDir = "/{}/".format(sCurUser)
                sAuthorDir = "/{}/".format(pubDstScn.author)
                for sCacheNode in sCacheNodeList:
                    sCacheDir = pathNorm(mc.getAttr(sCacheNode + ".cachePath"))
                    sCacheName = mc.getAttr(sCacheNode + ".cacheName")
                    sCachePath = mc.cacheFile(sCacheNode, q=True, fileName=True)
                    if (not sCachePath) and (sCurUserDir in sCacheDir):
                        print sCacheDir, sCacheName
                        sCacheDir = sCacheDir.replace(sCurUserDir, sAuthorDir)
                        print "--->", sCacheDir, sCacheName
                        mc.setAttr(sCacheNode + ".cachePath", sCacheDir, type="string")

            dependDct = dependency_scan.launch(srcScnInfos, among=sNodeList,
                                               modal=(not dryRun), okLabel="Publish",
                                               errorToWarning=("FileNotFound", "NameAlreadyUsed"))
            if not dependDct:
                print " No dependencies to publish ".center(80, "!")
        else:
            print " No 'cacheFile' nodes found ".center(80, "!")

        if publish:
            scnInfos = myagen.infosFromScene()

            if dependDct:
                damShot = scnInfos["dam_entity"]
                cacheDir = damShot.getResource("public", "charFx_cache_dir")
                if not dryRun:
                    cacheDir.setSyncRules(["no_sync"])

            scnMng = sceneManager.SceneManager(scnInfos)
            scnMng.publish(comment=sComment, sgVersionData=sgVersData,
                           dependencies=dependDct, dryRun=dryRun, autoUnlock=False)
    finally:
        if publish:
            pubDstScn.setLocked(False)


def _submitAnim(**kwargs):

    sShotName = kwargs.pop("shot")
    iStep = kwargs.pop("step", None)
    bNoSubmit = kwargs.get("noSubmit", False)

    for sLyrPath in damutils.iterLatestOutputLayers(sShotName, "left"):
        numFrames = len(os.listdir(sLyrPath))
        if numFrames > 1:
            continue

        sRndLyr = osp.basename(sLyrPath).rsplit("-v", 1)[0]
        if mc.objExists(sRndLyr) and (mc.nodeType(sRndLyr) == "renderLayer"):
            if numFrames == 0:
                raise EnvironmentError("'{}' has NO rendered image in '{}'"
                                       .format(sRndLyr, sLyrPath))
            elif numFrames == 1:
                sEndFrameAttr = "defaultRenderGlobals.endFrame"
                sMsg = "1 frame found in '{}'...\n".format(sLyrPath)
                sMsg += "...so overriding '{}' to 101 for '{}'".format(sEndFrameAttr,
                                                                       sRndLyr)
                pm.displayWarning(sMsg)
                mc.editRenderLayerAdjustment(sEndFrameAttr, layer=sRndLyr)
                mc.setAttr(sEndFrameAttr, 101)
        elif numFrames == 1:
            pm.displayError("No such renderLayer: '{}'".format(sRndLyr))

    curStep = mc.getAttr("defaultRenderGlobals.byFrameStep")
    try:
        if iStep:
            mc.setAttr("defaultRenderGlobals.byFrameStep", iStep)

        sFilePath = mc.rrSubmitZomb(**kwargs)

        if bNoSubmit:
            print "\n", sFilePath.center(120, "-")
            with open(sFilePath, 'r') as fileobj:
                for l in fileobj:
                    print l.strip()
            print sFilePath.center(120, "-"), "\n"
    finally:
        mc.setAttr("defaultRenderGlobals.byFrameStep", curStep)

def _submitFrame(**kwargs):

    iFrame = kwargs.pop("frame")
    bNoSubmit = kwargs.get("noSubmit", False)

    curStart = mc.getAttr("defaultRenderGlobals.startFrame")
    curEnd = mc.getAttr("defaultRenderGlobals.endFrame")
    curStep = mc.getAttr("defaultRenderGlobals.byFrameStep")
    try:
        mc.setAttr("defaultRenderGlobals.byFrameStep", 1.0)
        mc.setAttr("defaultRenderGlobals.startFrame", iFrame)
        mc.setAttr("defaultRenderGlobals.endFrame", iFrame)

        sFilePath = mc.rrSubmitZomb(**kwargs)

        if bNoSubmit:
            print "\n", sFilePath.center(120, "-")
            with open(sFilePath, 'r') as fileobj:
                for l in fileobj:
                    print l.strip()
            print sFilePath.center(120, "-"), "\n"
    finally:
        mc.setAttr("defaultRenderGlobals.byFrameStep", curStep)
        mc.setAttr("defaultRenderGlobals.startFrame", curStart)
        mc.setAttr("defaultRenderGlobals.endFrame", curEnd)

def submitElBorgno(sSrcScnPath, stills=False, dryRun=False):

    mc.loadPlugin("rrSubmit_Maya_Z2K.py")

    srcScnInfos = myagen.infosFromScene(sSrcScnPath)
    damShot = srcScnInfos["dam_entity"]
    proj = damShot.project
    sShotName = damShot.name

    srcScn = srcScnInfos["rc_entry"]
    bPublicSrc = srcScn.isPublic()
    if bPublicSrc and not srcScn.isVersionFile():
        raise ValueError("Source scene is NOT a version file: '{}'"
                         .format(sSrcScnPath))

    filters = [ ['project', 'is', {'type':'Project', 'id':67}],
                ['content', 'in', ("rendering", "render_stereo")],
                ['entity.Shot.code', 'is', sShotName], ]
    fields = ["content", "entity.Shot.code", "sg_status_list", "sg_operators", "sg_keyframe"]
    sgTaskList = proj._shotgundb.sg.find("Task", filters, fields)
    if not sgTaskList:
        raise EnvironmentError("No rendering tasks found for '{}'".format(sShotName))

    sgTaskDct = dict((d["content"], d) for d in sgTaskList)
    sgStereoTask = sgTaskDct["render_stereo"]

    iFrameList = iStep = None
    if stills:
        sgRenderTask = sgTaskDct["rendering"]
        sKeyFrame = sgRenderTask["sg_keyframe"]
        sFrameList = re.findall("[^\s,]+", sKeyFrame.lower())
        if 'step' in sFrameList:
            i = sFrameList.index('step')
            iStep = int(sFrameList[i + 1])
            sFrameList.remove('step')
            del sFrameList[i + 1]
        iFrameList = tuple(int(s) for s in sFrameList)

    sVersSuffix = mkVersionSuffix(srcScn.versionFromName())
    headFile = srcScn.getHeadFile(dbNode=False)

    sSuffix = "".join((sVersSuffix, "-elborgno"))
    privScn, bCopied = headFile.copyToPrivateSpace(suffix=sSuffix, existing="keep",
                                                   sourceFile=srcScn)
    sSrcScnPath = privScn.absPath()
    bSrcScnExists = (not bCopied)
    try:
        if bSrcScnExists:
            print (" '{}' already exists: submitting without changes "
                   .format(privScn.name).center(120, "-"))
            myasys.openScene(sSrcScnPath, force=True, fail=False, lrd="none")
        else:
            myasys.openScene(sSrcScnPath, force=True, fail=False)

            rendering.updateStereoCam(gui=False)
            rendering.renderRightCam()

            pm.saveFile(force=True)

        sCieProjName = "el-borgno"
        if stills:
            sCieProjName += "-stills"
        else:
            sCieProjName += "-anim"

        if dryRun:
            sCieProjName += "-test"

        params = [
        "PreviewGamma2.2=" + '0~1',
        "DefaultClientGroup=" + '1~ALL',
        "CustomUserInfo=" + '1~0~Rendu El Borgno',
        "CompanyProjectName=" + '0~{}'.format(sCieProjName),
        "CustomVersionName=" + '0~{}'.format(sVersSuffix.strip("-")),
        "Color_ID=" + '1~11']

        if dryRun:
            params.append("SendJobDisabled=" + '1~1')

        if iFrameList:
            for iFrame in iFrameList:
                _submitFrame(frame=iFrame, noSubmit=False, parameter=params)

        if (not stills) or (stills and iStep):
            _submitAnim(shot=sShotName, noSubmit=False, parameter=params, step=iStep)

    except Exception as e:
        if not bSrcScnExists:
            try:
                os.remove(sSrcScnPath)
            except OSError:
                traceback.print_exc()
        raise e

    if not dryRun:
        sDetailStatus = "stills en calcul" if stills else "anim en calcul"
        pprint(proj.updateSgEntity(sgStereoTask, sg_status_list="clc",
                                   sg_detail_status=sDetailStatus))

