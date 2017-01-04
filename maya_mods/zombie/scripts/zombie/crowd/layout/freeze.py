
from pprint import pprint

import maya.cmds as mc
import pymel.core as pm
import pymel.util as pmu

from pytd.util.qtutils import setWaitCursor

from pytaya.core import rendering as mrender
from pytaya.util.sysutils import withSelectionRestored

from dminutes import geocaching
from davos.core.damproject import DamProject
from pytaya.core.general import lsNodes

reload(geocaching)

def getShader(oMesh, sSgAttr):

    oMatList = mrender.shadersFromObjects([oMesh], connectedTo=sSgAttr)
    if not oMatList:
        return None

    oMatList = tuple(o for o in oMatList if not o.isShared())
    if not oMatList:
        return None

    return oMatList[0]

def stripNamespace(sObjName):
    return sObjName.rsplit(":", 1)[-1]

@setWaitCursor
def mergeShaders(sGeoGrpList):

    proj = DamProject("zombillenium", empty=True)

    variaDct = {}
    sErrorList = []
    for sGeoGrp in sGeoGrpList:

        sNmspc = geocaching.getNamespace(sGeoGrp)
        sAstName = "_".join(sNmspc.split("_")[:3])
        iVaria = mc.getAttr(sGeoGrp + ".variationChoice")

        oMeshList = pm.ls(sGeoGrp, dag=True, type="mesh", ni=True)

        for oMesh in oMeshList:

            choiceDct = {}

            oMat = getShader(oMesh, "surfaceShader")
            if not oMat:
                continue

            if not oMat.parentNamespace().startswith(sAstName + "_"):
                print "colors already frozen:", oMesh, oMat
                continue

            sLyrTexList = mc.listConnections(oMat.name(), s=True, d=False, type="layeredTexture")
            if sLyrTexList:
                sLyrTex = sLyrTexList[0]
                sCurAttr = sLyrTex + ".inputs[{}].color".format(iVaria)
                print oMesh, oMat, sCurAttr
                sInColorAttr = mc.listConnections(sCurAttr, s=True, d=False, plugs=True)
                sInColorAttr = sInColorAttr[0]
                choiceDct[stripNamespace(sLyrTex)] = stripNamespace(sInColorAttr)

            oAiMat = getShader(oMesh, "aiSurfaceShader")
            sAlSwitchList = mc.listConnections(oAiMat.name(), s=True, d=False, type="alSwitchColor")
            if sAlSwitchList:
                for sAlSwitch in set(sAlSwitchList):
                    iCurMix = int(mc.getAttr(sAlSwitch + ".mix"))
                    sCurAttr = sAlSwitch + ".input" + chr(iCurMix + 97).upper()
                    print oMesh, oAiMat, sCurAttr
                    sInList = mc.listConnections(sCurAttr, s=True, d=False, plugs=True)
                    if sInList:
                        colorChoice = stripNamespace(sInList[0])
                    else:
                        sErrorList.append("No color connected to '{}'".format(sCurAttr))
                        colorChoice = mc.getAttr(sCurAttr)[0]

                    choiceDct[stripNamespace(sAlSwitch)] = colorChoice

            sMatList = (oMat.name(), oAiMat.name())
            variaDct.setdefault(sAstName, {}).setdefault(unicode(oMat.stripNamespace()), []).append((oMesh, choiceDct, sMatList))

    if sErrorList:
        raise RuntimeError("\n".join(sErrorList))

    #pprint(variaDct)
    #raise RuntimeError("prout")

#    sImportedList = []
    sMergedMatList = []

    for sAstName, switchItemsDct in variaDct.iteritems():

        if not mc.ls(sAstName + "_*", type="lambert"):
            damAst = proj.getAsset(sAstName)
            p = damAst.getPath("public", "render_ref")
            sNewNodeList = mc.file(p, i=True, returnNewNodes=True,
                                   renameAll=True, renamingPrefix=sAstName)
            sDagList = mc.ls(sNewNodeList, type="dagNode")
            if sDagList:
                mc.delete(sDagList)

#            mc.refresh()
#            sNewNodeList = mc.ls(sNewNodeList)
#            if sNewNodeList:
#                sImportedList.extend(sNewNodeList)

        for sMatName, switchItems in switchItemsDct.iteritems():

            sNewMatName = sAstName + "_" + sMatName
            sNewMat = geocaching.getNode(sNewMatName)
            if not sNewMat:
                pm.displayWarning("Shader not found: '{}'".format(sNewMatName))
                continue

            sSwNodeDct = {}
            sOldMatSet = set()
            sMeshList = []
            for oMesh, choiceDct, sMatList in switchItems:

                sMesh = oMesh.name()
                sMeshList.append(sMesh)
                sOldMatSet.update(sMatList)

                if not choiceDct:
                    continue

                for sChoiceNode, colorChoice in choiceDct.iteritems():

                    sSwitchName = sAstName + "_" + sChoiceNode
                    if "_layeredTexture" in sSwitchName:
                        sSwitchName = sSwitchName.replace("_layeredTexture", "_tripleShadingSwitch")
                    elif "_alSwitchColor" in sSwitchName:
                        sSwitchName = sSwitchName.replace("_alSwitchColor", "_tripleShadingSwitch")
                    else:
                        sSwitchName = sSwitchName + "_tripleShadingSwitch"

                    sSwitchNode = geocaching.getNode(sSwitchName)
                    if not sSwitchNode:
                        sSwitchNode = mc.shadingNode("tripleShadingSwitch",
                                                     name=sSwitchName,
                                                     asUtility=True)

                    print sAstName + "_" + sChoiceNode, sSwitchNode
                    sSwNodeDct[sChoiceNode] = sSwitchNode

                    if isinstance(colorChoice, basestring):
                        sChoiceAttr = sAstName + "_" + colorChoice
                        ids = mc.getAttr(sSwitchNode + ".input", multiIndices=True)
                        idx = (ids[-1] + 1) if ids else 0
                        sInSwitchAttr = sSwitchNode + ".input[{}]".format(idx)
                        mc.connectAttr(sMesh + ".instObjGroups[0]", sInSwitchAttr + ".inShape")
                        mc.connectAttr(sChoiceAttr, sInSwitchAttr + ".inTriple")
                    elif isinstance(colorChoice, tuple):
                        print str(colorChoice).center(120, "!")

            for sChoiceNode, sSwitchNode in sSwNodeDct.iteritems():
                sOutList = mc.listConnections(sAstName + "_" + sChoiceNode, s=False, d=True, plugs=True)
                if not sOutList:
                    continue
                for sOutAttr in sOutList:
                    mc.connectAttr(sSwitchNode + ".output", sOutAttr, f=True)

            mc.select(sMeshList, replace=True)
            mc.hyperShade(assign=sNewMat)

            sMergedMatList.extend(sOldMatSet)

    return sMergedMatList

@withSelectionRestored
def freeze():

    sGeoGrpList, _ = geocaching._confirmProcessing("Freeze crowd", confirm=True,
                                                   regexp="^cwp_", selected=None, fromShapes=False)
    #sGeoGrpList = tuple(s for s in sGeoGrpList if mc.referenceQuery(s, isNodeReferenced=True))

    if  not sGeoGrpList:
        mc.warning("No crowd to freeze.")
        return

    oRefList = []
    for sGeoGrp in sGeoGrpList:
        if mc.referenceQuery(sGeoGrp, isNodeReferenced=True):
            oRef = pm.FileReference(mc.referenceQuery(sGeoGrp, referenceNode=True))
            oRefList.append(oRef)

    for oRef in oRefList:
        oRef.importContents()
        
    mc.refresh()

    sMergedMatList = mergeShaders(sGeoGrpList)

    if sMergedMatList:
        #mc.refresh()
        sMergedMatList = lsNodes(sMergedMatList, not_rn=True, nodeNames=True)
        pm.displayInfo("{} shaders to delete".format(len(sMergedMatList)))
        sDelList = []
        for sMat in sMergedMatList:
            sHistList = mc.listHistory(sMat, ac=True, pdo=True)
            if sHistList:
                sDelList.extend(sHistList)
        if sDelList:
            pm.displayInfo("deleting {} shading nodes".format(len(sDelList)))
            mc.delete(sDelList)

    for sGeoGrp in sGeoGrpList:
        sAttr = sGeoGrp + ".variationChoice"
        if mc.objExists(sAttr):
            mc.setAttr(sAttr, lock=True)

    mc.refresh()

    for sGeoGrp in sGeoGrpList:

        sObjList = mc.ls(sGeoGrp, dag=True, type="mesh", ni=True)
        #mc.delete(sObjList, ch=True)
        mc.bakePartialHistory(sObjList, prePostDeformers=True)

        sAttr = sGeoGrp + ".animationChoice"
        if mc.objExists(sAttr):
            mc.setAttr(sAttr, lock=True)

    mc.refresh()

    for sGeoGrp in sGeoGrpList:
        sNmspc = geocaching.getNamespace(sGeoGrp)

        sDstAttr = sNmspc + ":grp_local.translateZ"
        sSrcAttrList = mc.listConnections(sDstAttr, s=True, d=False, p=True)
        if not sSrcAttrList:
            continue

        sSrcAttr = sSrcAttrList[0]
        mc.disconnectAttr(sSrcAttr, sDstAttr)
        sHistList = mc.listHistory(sSrcAttr.rsplit(".", 1)[0], pdo=True, ac=True)
        if sHistList:
            sHistList = lsNodes(sHistList, not_defaultNodes=True)
            if sHistList:
                pm.displayInfo("delete {} input nodes on {}"
                               .format(len(sHistList), sDstAttr))
                mc.delete(sHistList)

#    # optimize scene
#    pmu.putEnv("MAYA_TESTING_CLEANUP", "1")
#    sCleanOptList = ("referencedOption", "shaderOption")
#    try:
#        if sImportedList:
#            mc.lockNode(sImportedList, lock=True)
#        pm.mel.source("cleanUpScene.mel")
#        pm.mel.scOpt_performOneCleanup(sCleanOptList)
#    finally:
#        pmu.putEnv("MAYA_TESTING_CLEANUP", "")
#        if sImportedList:
#            mc.lockNode(sImportedList, lock=False)

    return

freeze()
