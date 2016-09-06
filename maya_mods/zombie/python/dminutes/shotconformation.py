import maya.cmds as mc
import pymel.core as pm

import os
import re

from davos_maya.tool.general import infosFromScene, assertSceneInfoMatches
from davos.core.damproject import DamProject

from dminutes import miscUtils
reload (miscUtils)




def removeRefEditByAttr(inRefNodeL=[], attr="smoothDrawType", cmd="setAttr",failedRefEdit =False, GUI=True):
    log = miscUtils.LogBuilder(gui=GUI, funcName ="removeRefEditByAttr")
    refNodeL = []

    sAttrList = attr if not isinstance(attr, basestring) else [attr]
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
                if sAttr in sAttrList:
                    sNodeAttrDct.setdefault(sAttr, set()).add(sNodeAttr)

            if not sNodeAttrDct:
                continue

            refIsLoaded = mc.referenceQuery(eachRefNode, isLoaded=True)
            if refIsLoaded:
                mc.file(unloadReference=eachRefNode)

            try:
                for sAttr, sNodeAttrSet in sNodeAttrDct.iteritems():
                    for sNodeAttr in sNodeAttrSet:
                        mc.referenceEdit(sNodeAttr, editCommand=sCmd, removeEdits=True,failedEdits=True, successfulEdits=True)
                        
                        sMsg = "'{}', '{} .{}' {} reference edit deleted".format(eachRefNode , sCmd, sAttr, len(sNodeAttrSet))
                    log.printL("i", sMsg)
            finally:
                if refIsLoaded:
                    mc.file(loadReference=eachRefNode)

        if failedRefEdit:
            mc.referenceEdit(eachRefNode, removeEdits=True,failedEdits=True,successfulEdits = False)
            sMsg = "'{}'  all failing reference edit  removed".format(eachRefNode)
            log.printL("i", sMsg)

    for each in log.logL:
        print each

    return log.resultB, log.logL


def finalLayoutToLighting(gui=True):
    log = miscUtils.LogBuilder(gui=gui, funcName ="finalLayoutToLighting")
    deletedNodeL=[]

    mc.editRenderLayerGlobals( currentRenderLayer='defaultRenderLayer' )

    mc.ls("cam_animatic:asset*")
    toDeleteNodeL=mc.ls("mat_arelequin_*")+mc.ls("aiAOV_arlequin*")+mc.ls("lay_finalLayout_*")+mc.ls("cam_animatic:asset*")
    for each in toDeleteNodeL: 
        try: 
            mc.delete(each)
            deletedNodeL.append(each)
        except Exception as err:
            print err
            pass

    removeRefEditByAttr(inRefNodeL=[], attr="aovName", cmd="setAttr", failedRefEdit =True, GUI=True)
    txt = "{} node(s) deleted: '{}': ".format(len(deletedNodeL),deletedNodeL)
    log.printL("i", txt)

    pm.mel.eval("source updateSoundMenu")
    pm.mel.eval("setSoundDisplay audio 0")
    log.printL("i", "sound turned off")


    miscUtils.deleteUnknownNodes()

    return dict(resultB=log.resultB, logL=log.logL)



def releaseShotAsset(gui = True ,toReleaseL = [], dryRun=True, astPrefix = "fx3"):
    log = miscUtils.LogBuilder(gui=gui, funcName ="releaseShotAsset")

    #proj = DamProject("zombillenium")
    #damShot = proj.getShot("sq0300_sh0120a")

    scnInfos = infosFromScene()
    damShot = scnInfos.get("dam_entity")
    privScnFile = scnInfos["rc_entry"]
    shotLib = damShot.project.getLibrary("public","shot_lib")

    sPublicReleaseDir = miscUtils.pathJoin(os.path.dirname(damShot.getPath("public", "fx3d_scene")),"release")
    sPrivReleaseDir = miscUtils.pathJoin(os.path.dirname(damShot.getPath("private", "fx3d_scene")),"release")

    # dir creation
    if not os.path.isdir(sPublicReleaseDir):
        os.makedirs(sPublicReleaseDir)
    if not os.path.isdir(sPrivReleaseDir):
        os.makedirs(sPrivReleaseDir)

    for each in toReleaseL:
        eachShort = each.split("|")[-1]
        if not re.match('^[a-zA-Z0-9]{3}_[a-zA-Z0-9]{1,16}_[a-zA-Z0-9]{1,16}$', eachShort) or eachShort.split("_")[0]!=astPrefix:
            txt = "'{}' doesn't match the naming convention: '{}_[a-zA-Z0-9](1,16)_[a-zA-Z0-9](1,16)'".format(eachShort, astPrefix)
            log.printL("e", txt)
            continue
        else:
            #export
            sPrivateFilePath=miscUtils.pathJoin(sPrivReleaseDir,each+".mb")
            sPublicFilePath=miscUtils.pathJoin(sPublicReleaseDir,each+".mb")
            if not dryRun:
                mc.file(sPrivateFilePath, force =True,  options="v=0;", typ="mayaBinary", preserveReferences=True, exportSelected=True, ch=True, chn=True, con=True, exp=True, sh=True)
                txt = "Exporting: {}".format(sPrivateFilePath)
                log.printL("i", txt)
            else:
                txt = "DryRun Exporting: {}".format(sPrivateFilePath)
                log.printL("i", txt)

            # let's publish
            sComment = "from v{}".format(privScnFile.versionFromName())
            releaseDir = shotLib.getEntry(sPublicReleaseDir)
            releaseDir.publishFile(sPrivateFilePath, autoLock=True, autoUnlock=True, comment=sComment, dryRun=dryRun, saveChecksum=False)

    return dict(resultB=log.resultB, logL=log.logL)

