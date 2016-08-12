
from collections import OrderedDict

import maya.cmds as mc
import pymel.core as pc

from davos_maya.tool import reference as myaref


def addNode(sNodeType, sNodeName, parent=None, unique=True, skipSelect=True):
    if unique and mc.objExists(sNodeName):
        return sNodeName
    return mc.createNode(sNodeType, parent=parent, name=sNodeName, skipSelect=skipSelect)

def getNode(sNodeName):
    return sNodeName if mc.objExists(sNodeName) else None

def objectSetMembers(sSetName, recursive=True):

    if not mc.objExists(sSetName):
        return set()

    sMemberSet = mc.sets(sSetName, q=True)
    if sMemberSet is None:
        return set()
    else:
        sMemberSet = set(mc.ls(sMemberSet, dag=True, ni=True) if recursive else sMemberSet)

    return sMemberSet

def clearObjectSet(sSetName):
    mc.sets(e=True, clear=sSetName)

def addToSmoothSet(sSetName, in_sAddList):

    sMemberSet = objectSetMembers(sSetName)
    if sMemberSet:
        sAddSet = set(in_sAddList) - sMemberSet
    else:
        sAddSet = set(in_sAddList)

    if sAddSet:
        sAddList = list(sAddSet)
        mc.sets(sAddList, e=True, include=sSetName)

        sDagSet = set(mc.ls(sAddList, dag=True, ni=True))
        sDelSet = (sMemberSet & sDagSet) - sAddSet
        if sDelSet:
            mc.sets(list(sDelSet), e=True, remove=sSetName)

    return sAddSet

def addToSmooth():

    sSelList = mc.ls(sl=True, type="dagNode")
    if not sSelList:
        return

    sCurObjSet = addNode("objectSet", "set_applySmoothOnCapture", unique=True)
    addToSmoothSet(sCurObjSet, sSelList)

    sNoSmoothSet = getNode("set_ignoreSmoothOnCapture")
    if sNoSmoothSet:
        sCommonList = mc.sets(sNoSmoothSet, intersection=sCurObjSet)
        if sCommonList:
            sDelList = sCommonList + sSelList
        else:
            sDelList = sSelList
        mc.sets(sDelList, remove=sNoSmoothSet)
        smoothSetToRenderLayer(sNoSmoothSet)

    smoothSetToRenderLayer(sCurObjSet)

def delFromSmooth():

    sSelList = mc.ls(sl=True, type="dagNode")
    if not sSelList:
        return

    sCurObjSet = addNode("objectSet", "set_ignoreSmoothOnCapture", unique=True)
    addToSmoothSet(sCurObjSet, sSelList)

    sSmoothSet = getNode("set_applySmoothOnCapture")
    if sSmoothSet:

#        sDiffList = mc.sets(sCurObjSet, subtract=sSmoothSet)
#        print sDiffList

        sCommonList = mc.sets(sSmoothSet, intersection=sCurObjSet)
        if sCommonList:
            sDelList = list(set(sCommonList + sSelList))
        else:
            sDelList = sSelList
        mc.sets(sDelList, remove=sSmoothSet)
        smoothSetToRenderLayer(sSmoothSet)

    smoothSetToRenderLayer(sCurObjSet)

def listMeshesToSmooth():

    sMemberList = list(objectSetMembers("set_applySmoothOnCapture")
                       - objectSetMembers("set_ignoreSmoothOnCapture"))
    if not sMemberList:
        return []

    return mc.ls(sMemberList, type="mesh", ni=True)

def smoothSetToRenderLayer(sSetName):

    return

    sRndLyr = sSetName.replace("set_", "rlyr_")
    if not mc.objExists(sRndLyr):
        sRndLyr = mc.createRenderLayer(name=sRndLyr, empty=True)

    sLyrMemberSet = mc.editRenderLayerMembers(sRndLyr, q=True, fn=True)
    if sLyrMemberSet:
        sLyrMemberSet = set(mc.ls(sLyrMemberSet))
    else:
        sLyrMemberSet = set()

    sSetMemberSet = objectSetMembers(sSetName, recursive=False)

    sAddList = list(sSetMemberSet - sLyrMemberSet)
    if sAddList:
        mc.editRenderLayerMembers(sRndLyr, *sAddList, noRecurse=True)

    sDelList = list(sLyrMemberSet - sSetMemberSet)
    if sDelList:
        mc.editRenderLayerMembers(sRndLyr, *sDelList, remove=True, noRecurse=True)

def listSmoothableMeshes(project=None, warn=True):

    from pytaya.util import apiutils as myapi

    maxFaxes = pc.optionVar["smpSizeOfMeshForWarning"]
    nonSmoothableList = []


    sAllMeshSet = set(listMeshesToSmooth())
    numMeshes = len(sAllMeshSet)
    numFailure = 0

    sPrevizMeshSet = set(myaref.listPrevizRefMeshes(project=project))
    if sPrevizMeshSet:
        sCommonSet = sAllMeshSet & sPrevizMeshSet
        if sCommonSet:
            cmnLen = len(sCommonSet)
            nonSmoothableList.append(("{} meshes".format(cmnLen), "from a previz file."))

            numFailure = cmnLen - 1
            sAllMeshSet -= sCommonSet

    smoothData = OrderedDict()

    numAllFaces = 0
    for sMesh in sAllMeshSet:

        sSmoothAttr = sMesh + ".displaySmoothMesh"

        value = mc.getAttr(sSmoothAttr)
        if value == 2:
            continue

        if mc.getAttr(sSmoothAttr, lock=True):
            nonSmoothableList.append((sMesh, "'displaySmoothMesh' attribute is locked."))
            continue

        dagPath = myapi.getDagPath(sMesh)
        if not dagPath.isVisible():
            continue

        meshInfo = mc.polyEvaluate(sMesh, triangle=True, face=True)
        numFaces = meshInfo["face"]
        if numFaces == meshInfo["triangle"]:
            nonSmoothableList.append((sMesh, "fully triangulated."))
            continue

        if numFaces >= maxFaxes:
            nonSmoothableList.append((sMesh, ("has {:,} faces, limit is {:,} faces."
                                              .format(numFaces, maxFaxes))))
            continue

        if mc.polyInfo(sMesh, nonManifoldEdges=True, nonManifoldVertices=True):
            nonSmoothableList.append((sMesh, "non-manifold."))
            continue

        numAllFaces += numFaces

        meshInfo[".displaySmoothMesh"] = value
        smoothData[sMesh] = meshInfo

    if warn and nonSmoothableList:

        numFailure += len(nonSmoothableList)

        w = len(max((n for n, _ in nonSmoothableList), key=len))
        def fmt(n, m):
            return "{0:<{2}}: {1}".format(n, m, w)

        sSep = "\n- "
        sMsgHeader = " {}/{} meshes will not be smoothed. ".format(numFailure, numMeshes)
        sMsgBody = sSep.join(fmt(n, m) for n, m in nonSmoothableList)
        sMsgEnd = "".center(100, "-")

        sMsg = '\n' + sMsgHeader.center(100, "-") + sSep + sMsgBody + '\n' + sMsgEnd
        print sMsg

        pc.displayWarning(sMsgHeader + "More details in Script Editor ----" + (70 * ">"))

    return smoothData, numAllFaces
