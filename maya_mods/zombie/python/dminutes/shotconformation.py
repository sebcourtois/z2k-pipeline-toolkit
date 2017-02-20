
import os
import re
from datetime import datetime
from fnmatch import fnmatch

import maya.cmds as mc
import pymel.core as pm
import pymel.util as pmu

from pytaya.core.general import lsNodes
from pytaya.core import cleaning

from davos_maya.tool.general import infosFromScene
#from davos.core.damproject import DamProject

from dminutes import miscUtils

reload (miscUtils)


def promptToContinue(exception):

    res = pm.confirmDialog(title='WARNING !',
                           message=exception.message,
                           button=['Continue', 'Abort'],
                           defaultButton='Abort',
                           cancelButton='Abort',
                           dismissString='Abort',
                           icon="warning")
    if res == "Abort":
        raise RuntimeWarning("Aborted !")

def assertTaskIsFinal(damShot, sTask, step="", sgEntity=None, critical=True):

    sgTask = damShot.getSgTask(sTask, step, sgEntity=sgEntity, fail=True)
    if sgTask["sg_status_list"] == "fin":
        return True

    err = AssertionError("Status of the {} task is not final yet."
                         .format("|".join(s for s in (step, sTask) if s)))
    if critical:
        raise err

    promptToContinue(err)

def removeRefEditByAttr(inRefNodeL=[], attr="smoothDrawType", cmd="setAttr",failedRefEdit =False, GUI=True):
    log = miscUtils.LogBuilder(gui=GUI, funcName ="removeRefEditByAttr")
    refNodeL = []

    sAttrPtrnList = attr if not isinstance(attr, basestring) else [attr]
    sCmdList = cmd if not isinstance(cmd, basestring) else [cmd]

    if not inRefNodeL:
        inRefNodeL = mc.ls(references=True)

    for each in inRefNodeL:
        try:
            mc.referenceQuery(each, filename=True)
        except RuntimeError as e:
            mc.warning(e.message.strip())
        else:
            refNodeL.append(each)

    for eachRefNode in refNodeL:
        for sCmd in sCmdList:
            sNodeAttrList = mc.referenceQuery(eachRefNode, editCommand=sCmd, editNodes=True, editAttrs=True)

            sNodeAttrDct = dict()
            for sNodeAttr in sNodeAttrList:
                sAttr = sNodeAttr.rsplit(".", 1)[1]
                for sPatrn in sAttrPtrnList:
                    if fnmatch(sAttr, sPatrn):
                        sNodeAttrDct.setdefault(sAttr, set()).add(sNodeAttr)
                        break

            if not sNodeAttrDct:
                continue

            refIsLoaded = mc.referenceQuery(eachRefNode, isLoaded=True)
            if refIsLoaded:
                mc.file(unloadReference=eachRefNode)

            try:
                for sAttr, sNodeAttrSet in sNodeAttrDct.iteritems():
                    for sNodeAttr in sNodeAttrSet:
                        mc.referenceEdit(sNodeAttr, editCommand=sCmd, removeEdits=True, failedEdits=True, successfulEdits=True)
                        
                    sMsg = ("'{}': removed {} '.{}' on {} node(s)"
                            .format(eachRefNode, sCmd, sAttr, len(sNodeAttrSet)))
                    log.printL("i", sMsg)
            finally:
                if refIsLoaded:
                    mc.file(loadReference=eachRefNode)

        if failedRefEdit:
            mc.referenceEdit(eachRefNode, removeEdits=True, failedEdits=True, successfulEdits=False)
            sMsg = "'{}'  all failing reference edit  removed".format(eachRefNode)
            log.printL("i", sMsg)

    if not mc.about(batch=True):
        for each in log.logL:
            print each

    return log.resultB, log.logL


def deleteFlRenderLayer(gui=True):
    log = miscUtils.LogBuilder(gui=gui, funcName="deleteFlRenderLayer")

    mc.editRenderLayerGlobals(currentRenderLayer='lay_finalLayout_00')

    testVisibilityL = (mc.ls('*:grp_*', type='transform') +
                       mc.ls('*:chr_*', type='transform') +
                       mc.ls('*:geo_*', type='transform'))
    visibilityL = []
    if testVisibilityL:
        for each in testVisibilityL:
            visibilityL.append(each + '.visibility')
    sHiddenList = list(sVizAttr.rsplit('.', 1)[0] for sVizAttr in visibilityL if not mc.getAttr(sVizAttr))

    mc.editRenderLayerGlobals(currentRenderLayer='defaultRenderLayer')

    if sHiddenList:
        mc.select(sHiddenList)
        pm.hide()
        txt = "{} node(s) hidden: '{}': ".format(len(sHiddenList), sHiddenList)
        log.printL("i", txt)

    for sOverAttr, override in miscUtils.iterRenderLayerOverrides("lay_finalLayout_00"):
        if not sOverAttr.endswith(".visibility"):
            continue
        try:
            if isinstance(override, basestring):
                if ("." in override) and mc.objExists(override):
                    if not mc.isConnected(override, sOverAttr , ignoreUnitConversion=True):
                        mc.connectAttr(override, sOverAttr, force=True)
                else:
                    mc.setAttr(sOverAttr, override, type="string")
            else:
                mc.setAttr(sOverAttr, override)
        except RuntimeError as e:
            pm.displayError(e)

    mc.delete('lay_finalLayout_00')

def finalLayoutToLighting(gui=True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="finalLayoutToLighting")
    deletedNodeL=[]

    bBatchMode = mc.about(batch=True)
    
    deleteFlRenderLayer(gui=gui)

    toDeleteNodeL = (mc.ls("mat_arelequin_*") +
                     mc.ls("mat_arlequin_*") +
                     mc.ls("aiAOV_arlequin*") +
                     mc.ls("cam_animatic:asset*") +
                     mc.ls("lay_finalLayout_*"))

    if toDeleteNodeL:
        for each in toDeleteNodeL:
            try:
                mc.delete(each)
            except Exception as err:
                pm.displayWarning(err)
            else:
                deletedNodeL.append(each)
        txt = "{} node(s) deleted: '{}': ".format(len(deletedNodeL), deletedNodeL)
        log.printL("i", txt)

    sAttrList = ("smoothDrawType", "displaySmoothMesh", "dispResolution",
                 "pnts", "pt[[]*[]]", "pnts[[]*[]]",
                 "uvsp[[]*[]]", "uvSetPoints[[]*[]]",
                 "uvSetName")
    removeRefEditByAttr([], attr=sAttrList, cmd=("setAttr",), GUI=True)

    cleaning.deleteAllJunkShapes()

    sJunkPolyTransList = []
    for each in lsNodes(nodeNames=True, type="polyTransfer", not_rn=True):
        if not mc.listConnections(each, s=True, d=True, plugs=True):
            sJunkPolyTransList.append(each)
    if sJunkPolyTransList:
        mc.delete(sJunkPolyTransList)
        txt = "{} 'polyTransfer' node(s) deleted: '{}': ".format(len(sJunkPolyTransList), sJunkPolyTransList)
        log.printL("i", txt)

    miscUtils.deleteUnknownNodes()
    sDirLightToHide = mc.ls('lgt_finalLayout_directional')
    if sDirLightToHide and not sDirLightToHide == None:
        mc.hide(sDirLightToHide)

    # optimize scene
    pmu.putEnv("MAYA_TESTING_CLEANUP", "1")
    sCleanOptList = ("referencedOption", "shaderOption")
    try:
        pm.mel.source("cleanUpScene.mel")
        pm.mel.scOpt_performOneCleanup(sCleanOptList)
    finally:
        pmu.putEnv("MAYA_TESTING_CLEANUP", "")

    if not bBatchMode:
        pm.mel.eval("source updateSoundMenu")
        pm.mel.eval("setSoundDisplay audio 0")
        log.printL("i", "sound turned off")

    return dict(resultB=log.resultB, logL=log.logL)


def releaseShotAsset(gui = True ,toReleaseL = [], dryRun=True, astPrefix = "fx3"):
    log = miscUtils.LogBuilder(gui=gui, funcName ="releaseShotAsset")

    scnInfos = infosFromScene()
    damShot = scnInfos.get("dam_entity")
    privScnFile = scnInfos["rc_entry"]
    shotLib = damShot.project.getLibrary("public","shot_lib")

    sPublicReleaseDir = miscUtils.pathJoin(os.path.dirname(damShot.getPath("public", "fx3d_scene")),"release")
    sPrivReleaseDir = miscUtils.pathJoin(os.path.dirname(damShot.getPath("private", "fx3d_scene")),"release")

    bRlsDirCreated = False
    # dir creation
    if not os.path.isdir(sPublicReleaseDir):
        os.makedirs(sPublicReleaseDir)
        bRlsDirCreated = True

    if not os.path.isdir(sPrivReleaseDir):
        os.makedirs(sPrivReleaseDir)

    releaseDir = shotLib.getEntry(sPublicReleaseDir)
    if bRlsDirCreated:
        releaseDir.setSyncRules(["all_sites"])

    intSelection = mc.ls(selection=True)
    for each in toReleaseL:
        mc.select(each,r=True)
        eachShort = each.split("|")[-1]
        if not re.match('^[a-zA-Z0-9]{3}_[a-zA-Z0-9]{1,16}_[a-zA-Z0-9]{1,16}$', eachShort) or eachShort.split("_")[0]!=astPrefix:
            txt = "'{}' doesn't match the naming convention: '{}_[a-zA-Z0-9](1,16)_[a-zA-Z0-9](1,16)'".format(eachShort, astPrefix)
            log.printL("e", txt)
            continue
        else:
            #export
            sPrivateFilePath=miscUtils.pathJoin(sPrivReleaseDir,each+".mb")
            #sPublicFilePath=miscUtils.pathJoin(sPublicReleaseDir,each+".mb")
            if not dryRun:
                mc.file(sPrivateFilePath, force=True, options="v=0;", typ="mayaBinary",
                        preserveReferences=True, exportSelected=True, ch=True,
                        chn=True, con=True, exp=True, sh=True)
                txt = "Exporting: {}".format(sPrivateFilePath)
                log.printL("i", txt)
            else:
                txt = "DryRun Exporting: {}".format(sPrivateFilePath)
                log.printL("i", txt)

            # let's publish
            sComment = "from v{}".format(privScnFile.versionFromName())
            releaseDir.publishFile(sPrivateFilePath, autoLock=True, autoUnlock=True,
                                   comment=sComment, dryRun=dryRun, saveChecksum=False)

    mc.select(intSelection,r=True)

    return dict(resultB=log.resultB, logL=log.logL)


def referenceShotAsset(gui = True , dryRun=False, astPrefix = "fx3", critical= True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="referenceShotAsset")

    #proj = DamProject("zombillenium")
    #shotNameS = pm.sceneName().split('shot/')[-1].split("/")[1]
    #damShot = proj.getShot(shotNameS)

    lPublicReleaseFilePath = []

    scnInfos = infosFromScene()
    damShot = scnInfos.get("dam_entity")
    privScnFile = scnInfos["rc_entry"]
    shotLib = damShot.project.getLibrary("public","shot_lib")

    sPublicReleaseDir = miscUtils.pathJoin(os.path.dirname(damShot.getPath("public", "fx3d_scene")),"release")

    resultD = getRefFileList(name=astPrefix+"_*")
    sceneRefFileL=resultD["refFilePathL"]

    if astPrefix == "fx3":
        sTask = "fx_precomp"
        assertTaskIsFinal(damShot, sTask, step="", sgEntity=None, critical=critical)


    # dir scan
    if not os.path.isdir(sPublicReleaseDir):
        txt = "Nothing to reference,'{}' doesn't exist".format(sPublicReleaseDir)
        log.printL("e", txt)
        return
    else:
        dirItemL = os.listdir(sPublicReleaseDir)
        if dirItemL:
            for each in dirItemL:
                if os.path.isfile(miscUtils.pathJoin(sPublicReleaseDir,each)) and re.match('^[a-zA-Z0-9]{3}_[a-zA-Z0-9]{1,16}_[a-zA-Z0-9]{1,16}.mb$', each) and each.split("_")[0]==astPrefix :
                    sPublicReleaseFilePath = miscUtils.pathJoin(sPublicReleaseDir,each)
                    if sPublicReleaseFilePath not in sceneRefFileL:
                        statInfo = os.stat(sPublicReleaseFilePath)
                        statDate = statInfo.st_mtime
                        statSize = statInfo.st_size
                        if statSize > 5000:
                            dateS = datetime.fromtimestamp(int(statDate)).strftime(u"%Y-%m-%d %H:%M")
                            lPublicReleaseFilePath.append(sPublicReleaseFilePath)
                            txt = "Referencing: '{}'  publish date: {}".format(sPublicReleaseFilePath, dateS)
                            log.printL("i", txt)
                            if not dryRun:
                                mc.file( sPublicReleaseFilePath, type= 'mayaBinary', ignoreVersion=True, namespace=each.split(".")[0]+"_1", preserveReferences= True, reference = True )
                            else:
                                log.printL("w", "dry run mode")
                        else:
                            txt = "skipping empty file: '{}'".format(sPublicReleaseFilePath)
                            log.printL("w", txt)
                    else:
                        txt = "skipping file is already referenced: '{}'".format(sPublicReleaseFilePath)
                        log.printL("w", txt)
                    
    return dict(resultB=log.resultB, logL=log.logL)



def getRefFileList(name="fx3_*" ):
    log = miscUtils.LogBuilder(gui=True, funcName ="getRefFileList")

    refFilePathL =[]
    refNodeFailedL=[]
    refNodeL = mc.ls(name, references=True)

    for each in refNodeL:
        try:
            refFilePathS = mc.referenceQuery(each, filename=True)
            refFilePathL.append(refFilePathS)
        except RuntimeError as e:
            mc.warning(e.message.strip())
        else:
            refNodeFailedL.append(each)
    
    return dict(resultB=log.resultB, logL=log.logL, refFilePathL=refFilePathL)

