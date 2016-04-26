

import os.path as osp

from pytd.util.fsutils import pathJoin
from pytd.util.sysutils import grouper

import maya.api.OpenMaya as om
import maya.cmds as mc

from pymel.util.arguments import listForNone
import pymel.core as pm

from pytaya.util import apiutils as myapi

from davos_maya.tool.general import entityFromScene

from dminutes import maya_scene_operations as mop

reload(mop)


LOGGING_SETS = []
UNUSED_TRANSFER_NODES = []

def getNamespace(sNode):
    return sNode.rsplit("|", 1)[-1].rsplit(":", 1)[0]

def iterConnectedAttrs(sNode, **kwargs):

    bSrc = kwargs.pop("source", kwargs.pop("s", True))
    bDst = kwargs.pop("destination", kwargs.pop("d", True))

    sConnList = mc.listConnections(sNode, s=bSrc, d=bDst, c=1, p=1)
    if sConnList:
        for i in xrange(0, len(sConnList), 2):
            yield sConnList[i].split(".", 1)[1]

def addLoggingSet(sName):

    global LOGGING_SETS

    sObjSet = mop.addNode("objectSet", "log_" + sName, unique=True)

    if sObjSet not in LOGGING_SETS:
        LOGGING_SETS.append(sObjSet)

    return sObjSet

def listChildMeshes(sXfm, longName=False):

    res = mc.listRelatives(sXfm, c=True, type="mesh", path=not longName, fullPath=longName)
    if not res:
        return []

    return mc.ls(res, ni=True)


def transferOutConnections(sSrcNode, sDstNode):

    sConnectList = mc.listConnections(sSrcNode, s=0, d=1, c=1, p=1)
    if not sConnectList:
        return

    sConnectList = tuple((s.split(".", 1)[-1], d) for s, d in grouper(2, sConnectList))
    for sSrcAttr, sDstPlug in sConnectList:
        mc.connectAttr(sDstNode + "." + sSrcAttr, sDstPlug, force=True)

def breakConnections(sSide, sNodeAttr):

    sValidSides = ("input", "output", "in", "out")
    if sSide not in sValidSides:
        raise ValueError("Invalid connection side given: '{}'. Expects: {}."
                         .format(sSide, sValidSides))

    bSrc = True if sSide.startswith("in") else False
    bDst = not bSrc

    sConnectList = mc.listConnections(sNodeAttr, s=bSrc, d=bDst, c=1, p=1)
    if not sConnectList:
        return

    sNode = sNodeAttr.split(".", 1)[0]

    sConnectList = list((cur, oth) for cur, oth in grouper(2, sConnectList)
                         if oth.split(".", 1)[0] != sNode)
    for sNodePlug, sOtherPlug in sConnectList:
        if bSrc:
            mc.disconnectAttr(sOtherPlug, sNodePlug)
        else:
            mc.disconnectAttr(sNodePlug, sOtherPlug)

    return sConnectList

@mop.withParallelEval
def exportCaches(**kwargs):

    damShot = entityFromScene()

    sAbcDirPath = mop.getAlembicCacheDir(damShot)

    frameRange = (pm.playbackOptions(q=True, animationStartTime=True),
                 pm.playbackOptions(q=True, animationEndTime=True))

    sJobList = []
    for sGeoGrp in mop.iterGeoGroups(**kwargs):
        sNmspc = getNamespace(sGeoGrp)
        sAbcPath = pathJoin(sAbcDirPath, sNmspc + "_cache.abc")
        sJob = ("-noNormals -uvWrite -writeVisibility -frameRange {range[0]} {range[1]} -root {root} -file {file}"
                .format(range=frameRange, root=sGeoGrp, file=sAbcPath))
        print sJob
        sJobList.append(sJob)

    mc.AbcExport(v=True, j=sJobList)

def iterTransformMapping(sSrcDagRoot, sTrgtNamespace, longName=False):

    oSrcDagRoot = pm.PyNode(sSrcDagRoot)
    sSrcNamespace = oSrcDagRoot.namespace()
    sSrcDagRoot = oSrcDagRoot.longName()

    if not sTrgtNamespace.endswith(":"):
        sTrgtNamespace += ":"

    if sSrcNamespace == sTrgtNamespace:
        raise ValueError("Same source and target namespaces given.")

    sTrgtDagRoot = oSrcDagRoot.nodeName().replace(sSrcNamespace, sTrgtNamespace)
    oTrgtDagRoot = pm.PyNode(sTrgtDagRoot)
    sTrgtDagRoot = oTrgtDagRoot.longName()

    sSrcDagList = mc.ls(sSrcDagRoot, dag=True, long=longName, ni=True)
    for sSrcDagPath in mc.ls(sSrcDagList, exactType="transform"):

        found = None
        if longName:
            sTrgtDagPath = sSrcDagPath.split(sSrcDagRoot, 1)[-1].replace(sSrcNamespace, sTrgtNamespace)
            sTrgtDagPath = sTrgtDagRoot + sTrgtDagPath
        else:
            sTrgtDagPath = sSrcDagPath.replace(sSrcNamespace, sTrgtNamespace)

        #print "\n", sSrcDagPath, "\n", sTrgtDagPath, "\n", sTrgtDagRoot

        if longName or ("|" in sTrgtDagPath):
            if mc.objExists(sTrgtDagPath) and mc.objectType(sTrgtDagPath, isType="transform"):
                found = sTrgtDagPath
        else:
            sFoundList = mc.ls(sTrgtDagPath, exactType="transform")
            if sFoundList:
                if len(sFoundList) == 1:
                    found = sFoundList[0]
                else:
                    pm.displayWarning("Multiple objects named '{}'".format(sTrgtDagPath))
                    found = sFoundList

        if not found:
            pm.displayWarning("No such object: '{}'".format(sTrgtDagPath))

        yield sSrcDagPath, found

def iterMatchedObjects(objMappingItems):
    for s, t in objMappingItems:
        if t and isinstance(t, basestring):
            yield s, t

def iterMeshMapping(xfmMappingItems, longName=False):

    for sSrcXfm, sTrgtXfm in iterMatchedObjects(xfmMappingItems):

        sMeshShapeList = listChildMeshes(sSrcXfm, longName=longName)
        if not sMeshShapeList:
            continue
        elif len(sMeshShapeList) > 1:
            pm.displayWarning("Multiple mesh shapes found under '{}'.".format(sSrcXfm))
            continue

        found = None

        sSrcMeshShape = sMeshShapeList[0]

        sMeshShapeList = listChildMeshes(sTrgtXfm, longName=longName)
        if sMeshShapeList:
            if len(sMeshShapeList) == 1:
                found = sMeshShapeList[0]
            else:
                pm.displayWarning("Multiple mesh shapes found under '{}'.".format(sTrgtXfm))
                found = sMeshShapeList
        else:
            pm.displayWarning("No mesh shape found under '{}'.".format(sTrgtXfm))

        yield sSrcMeshShape, found

def filteredXfmAttrs(sXfm):

    flags = dict(unlocked=True, connectable=True, scalar=True)

    sAttrSet = set(listForNone(mc.listAttr(sXfm, keyable=True, **flags)))
    sAttrSet.update(listForNone(mc.listAttr(sXfm, userDefined=True, **flags)))
    return sAttrSet

def connectTransforms(astToAbcXfmItems):

    sLockedList = []

    for sAstXfm, sAbcXfm in iterMatchedObjects(astToAbcXfmItems):

        astXfmPath = myapi.getDagPath(sAstXfm)
        if astXfmPath.isInstanced():
            n = astXfmPath.instanceNumber()
            if n > 0:
                pm.displayInfo("Instanced copy number {} ignored: '{}'"
                               .format(n, sAstXfm))
                continue

        if mc.lockNode(sAstXfm, q=True, lock=True)[0]:
            pm.displayWarning("Locked node ignored: '{}'".format(sAstXfm))
            sLockedList.append(sAstXfm)
            continue

        sAbcAttrSet = set(iterConnectedAttrs(sAbcXfm, s=True, d=False))
        sAbcAttrSet.update(filteredXfmAttrs(sAbcXfm))

        sAttrList = list(filteredXfmAttrs(sAstXfm) & sAbcAttrSet)
        for sAttr in sAttrList:
            breakConnections("input", sAstXfm + "." + sAttr)

        mc.copyAttr(sAbcXfm, sAstXfm, values=True, inConnections=True,
                    keepSourceConnections=True, at=sAttrList)

    if sLockedList:
        sNmspc = getNamespace(sLockedList[0])
        sObjSet = addLoggingSet("lockedNodes_" + sNmspc)
        mc.sets(sLockedList, e=True, include=sObjSet)

    return True

def _delUnusedTransferNodes():

    global UNUSED_TRANSFER_NODES

    if not UNUSED_TRANSFER_NODES:
        return

    sDelList = []
    for sPolyTrans in UNUSED_TRANSFER_NODES:
        breakConnections("out", sPolyTrans)
        sHistList = mc.ls(mc.listHistory(sPolyTrans + ".inputPolymesh", il=2), io=1, type="mesh")
        if not sHistList:
            continue
        sMeshShape = sHistList[0].split(".", 1)[0]
        sDelList.append(sMeshShape)

#    mc.refresh()
#    mc.delete(UNUSED_TRANSFER_NODES)
#    mc.refresh()
#    mc.delete(sDelList)
#    mc.refresh()

def connectMeshShapes(astToAbcMeshItems):

    global UNUSED_TRANSFER_NODES

    sLockedList = []
    sVertsDifferList = []
    sFacesDifferList = []
    sHasHistoryList = []

    for sAstMeshShape, sAbcMeshShape in iterMatchedObjects(astToAbcMeshItems):

        astMeshPath = myapi.getDagPath(sAstMeshShape)
        if astMeshPath.isInstanced():
            n = astMeshPath.instanceNumber()
            if n > 0:
                pm.displayInfo("Instanced copy number {} ignored: '{}'"
                               .format(n, sAstMeshShape))
                continue

        if mc.lockNode(sAstMeshShape, q=True, lock=True)[0]:
            pm.displayWarning("Locked node ignored: '{}'".format(sAstMeshShape))
            sLockedList.append(sAstMeshShape)
            continue

        if mc.listConnections(sAstMeshShape + ".inMesh", s=True, d=False):
            sHasHistoryList.append(sAstMeshShape)
            pm.displayWarning("Mesh with history ignored: '{}'".format(sAstMeshShape))
            continue

        abcMeshStat = mc.polyEvaluate(sAbcMeshShape, v=True, f=True)
        astMeshStat = mc.polyEvaluate(sAstMeshShape, v=True, f=True)

        if abcMeshStat != astMeshStat:
            if abcMeshStat["vertex"] != astMeshStat["vertex"]:
                sMsg = "Number of vertices differs:"
                sMsg += "\n    - '{}': {} verts".format(sAbcMeshShape, abcMeshStat["vertex"])
                sMsg += "\n    - '{}': {} verts".format(sAstMeshShape, astMeshStat["vertex"])
                pm.displayWarning(sMsg)
                sVertsDifferList.extend((sAbcMeshShape, sAstMeshShape))
                continue
            elif abcMeshStat["face"] != astMeshStat["face"]:
                sMsg = "Number of faces differs:"
                sMsg += "\n    - '{}': {} faces".format(sAbcMeshShape, abcMeshStat["face"])
                sMsg += "\n    - '{}': {} faces".format(sAstMeshShape, astMeshStat["face"])
                pm.displayInfo(sMsg)
                sFacesDifferList.extend((sAbcMeshShape, sAstMeshShape))

        sAbcOutAttr = mc.listConnections(sAbcMeshShape, s=True, d=False,
                                         type="AlembicNode", plugs=True)
        bDeformedMesh = False
        if sAbcOutAttr:
            sAbcOutAttr = sAbcOutAttr[0]
            bDeformedMesh = True

        if bDeformedMesh or mc.referenceQuery(sAstMeshShape, isNodeReferenced=True):
            sPolyTrans = mc.polyTransfer(sAstMeshShape, ao=sAbcMeshShape,
                                         uv=False, v=True, vc=False, ch=True)[0]
            if bDeformedMesh:
                mc.connectAttr(sAbcOutAttr, sPolyTrans + ".otherPoly", f=True)
        else:
            srcMesh = om.MFnMesh(myapi.getDagPath(sAbcMeshShape))
            dstMesh = om.MFnMesh(astMeshPath)
            dstMesh.setPoints(srcMesh.getPoints())

    if sLockedList:
        sNmspc = getNamespace(sLockedList[0])
        sObjSet = addLoggingSet("lockedNodes_" + sNmspc)
        mc.sets(sLockedList, e=True, include=sObjSet)

    if sHasHistoryList:
        sNmspc = getNamespace(sHasHistoryList[0])
        sObjSet = addLoggingSet("hasHistory_" + sNmspc)
        mc.sets(sHasHistoryList, e=True, include=sObjSet)

    if sVertsDifferList:
        sObjSet = addLoggingSet("VERTICES_MISMATCH")
        mc.sets(sVertsDifferList, e=True, include=sObjSet)

    if sFacesDifferList:
        sObjSet = addLoggingSet("FACES_MISMATCH")
        mc.sets(sFacesDifferList, e=True, include=sObjSet)

def importCaches(**kwargs):

    damShot = entityFromScene()
    sAbcDirPath = mop.getAlembicCacheDir(damShot)

    oAbcRefList = []

    for sAstGeoGrp in mop.iterGeoGroups(**kwargs):

        sAstNmspc = sAstGeoGrp.rsplit("|", 1)[-1].rsplit(":", 1)[0]
        sBaseName = sAstNmspc + "_cache"
        sAbcPath = pathJoin(sAbcDirPath, sBaseName + ".abc")

        if not osp.isfile(sAbcPath):
            pm.displayWarning("No such alembic file: '{}'".format(sAbcPath))
            continue

        print "\nImporting caches from '{}'".format(sAbcPath)

        sNewNodeList = mc.file(sAbcPath, type="Alembic", r=True, ns=sBaseName,
                               rnn=True, mergeNamespacesOnClash=False, gl=True)

        oAbcRef = pm.PyNode(sNewNodeList[0]).referenceFile()
        oAbcRefList.append(oAbcRef)
        sAbcNmspc = oAbcRef.namespace

        sObjSet = ""
        astToAbcXfmItems = tuple(iterTransformMapping(sAstGeoGrp, sAbcNmspc))
        sMemberList = tuple(s for s, t in astToAbcXfmItems if not t)
        if sMemberList:
            sObjSet = addLoggingSet("noMatch_" + sAbcNmspc)
            mc.sets(sMemberList, e=True, include=sObjSet)

        sMemberList = tuple(s for s, t in astToAbcXfmItems if isinstance(t, (tuple, list)))
        if sMemberList:
            sObjSet = addLoggingSet("multiMatches_" + sAbcNmspc)
            mc.sets(sMemberList, e=True, include=sObjSet)

        astToAbcMeshItems = tuple(iterMeshMapping(astToAbcXfmItems))
        sMemberList = tuple(s for s, t in astToAbcMeshItems if not t)
        if sMemberList:
            if not sObjSet:
                sObjSet = addLoggingSet("noMatch_" + sAbcNmspc)
            mc.sets(sMemberList, e=True, include=sObjSet)

        sMemberList = tuple(s for s, t in astToAbcMeshItems if isinstance(t, (tuple, list)))
        if sMemberList:
            if not sObjSet:
                sObjSet = addLoggingSet("multiMatches_" + sAbcNmspc)
            mc.sets(sMemberList, e=True, include=sObjSet)

        connectTransforms(astToAbcXfmItems)

        sRefAbcNode = ""
        sFoundList = mc.ls(sNewNodeList, type="AlembicNode")
        if sFoundList:
            #pm.displayInfo("No Alembic Node imported !")
            sRefAbcNode = sFoundList[0]

        connectMeshShapes(astToAbcMeshItems)

        if sRefAbcNode:
            sDupAbcNode = mc.duplicate(sRefAbcNode, ic=True)[0]
            transferOutConnections(sRefAbcNode, sDupAbcNode)

    mc.refresh()

    bRemoveRefs = False

    sRefNodeSet = set()
    sLogSetName = "log_CACHE_IMPORT"
    if LOGGING_SETS:
        oObjSet = pm.sets(LOGGING_SETS, n=sLogSetName)
        if bRemoveRefs:
            sRefNodeSet = set(pm.referenceQuery(oObj, referenceNode=True, topReference=True)
                              for oObj in oObjSet.flattened() if oObj.isReferenced())

    if bRemoveRefs:
        for i, oAbcRef in enumerate(oAbcRefList):
            if oAbcRef.refNode.name() not in sRefNodeSet:
                oAbcRef.remove()
                oAbcRefList[i] = None

        if oAbcRefList:
            print "\nReferences kept because some of their objects appear in '{}' set:".format(sLogSetName)
            for oAbcRef in oAbcRefList:
                if oAbcRef:
                    print "    - '{}': '{}'".format(oAbcRef.refNode, oAbcRef)
