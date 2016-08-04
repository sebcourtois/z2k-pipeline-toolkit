import maya.cmds as mc
import pymel.core as pm

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

    mc.ls("mat_arelequin_*")+mc.ls("aiAOV_arlequin*")
    toDeleteNodeL=mc.ls("mat_arelequin_*")+mc.ls("aiAOV_arlequin*")+mc.ls("lay_finalLayout_*")
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

    return dict(resultB=log.resultB, logL=log.logL)

