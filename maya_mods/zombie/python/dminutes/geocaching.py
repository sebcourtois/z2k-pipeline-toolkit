
import os
import os.path as osp

from pytd.util.fsutils import pathJoin
from pytd.util.sysutils import grouper, argToSet

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

    sConnectList = mc.listConnections(sSrcNode, s=False, d=True, c=True, p=True,
                                      skipConversionNodes=True)
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

    sAbcDirPath = mop.getAlembicCacheDir(damShot).replace("\\", "/")
    if not osp.exists(sAbcDirPath):
        os.makedirs(sAbcDirPath)

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

    return mc.AbcExport(v=True, j=sJobList)

def getTransformMapping(sSrcDagRoot, sTrgtNamespace, consider=None, longName=False):

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

    sConsiderList = mc.ls(consider, long=longName, ni=True) if consider else None
    canLog = lambda s: (not sConsiderList) or (sConsiderList and (s in sConsiderList))

    mappingItems = mc.ls(sSrcDagRoot, dag=True, long=longName, ni=True)
    mappingItems = mc.ls(mappingItems, exactType="transform", long=longName)

    sNoMatchList = []
    sMultiMatchList = []
    sLockedList = []
    #mappingItems = sSrcDagList[:]

    for i, sSrcDagPath in enumerate(mappingItems):

        found = None

        if mc.lockNode(sSrcDagPath, q=True, lock=True)[0]:
            if canLog(sSrcDagPath):
                pm.displayWarning("Locked node ignored: '{}'".format(sSrcDagPath))
                sLockedList.append(sSrcDagPath)
            continue

        srcDagPath = myapi.getDagPath(sSrcDagPath)
        if srcDagPath.isInstanced():
            n = srcDagPath.instanceNumber()
            if n > 0:
                if canLog(sSrcDagPath):
                    pm.displayInfo("Instanced copy number {} ignored: '{}'"
                                   .format(n, sSrcDagPath))
                continue

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
                    if canLog(sSrcDagPath):
                        pm.displayWarning("Multiple objects named '{}'".format(sTrgtDagPath))
                        sMultiMatchList.append(sSrcDagPath)
                    found = sFoundList

        if not found:
            if canLog(sSrcDagPath):
                pm.displayWarning("No such object: '{}'".format(sTrgtDagPath))
                sNoMatchList.append(sSrcDagPath)

        mappingItems[i] = (sSrcDagPath, found)

    if sLockedList:
        sObjSet = addLoggingSet("lockedNodes_" + sSrcNamespace.strip(":"))
        mc.sets(sLockedList, e=True, include=sObjSet)

    if sNoMatchList:
        sObjSet = addLoggingSet("noObjMatch_" + sSrcNamespace.strip(":"))
        mc.sets(sNoMatchList, e=True, include=sObjSet)

    if sMultiMatchList:
        sObjSet = addLoggingSet("multiObjsMatch_" + sSrcNamespace.strip(":"))
        mc.sets(sMultiMatchList, e=True, include=sObjSet)

    return tuple(itm for itm in mappingItems if not isinstance(itm, basestring))

def iterMatchedObjects(objMappingItems):
    for s, t in objMappingItems:
        if t and isinstance(t, basestring):
            yield s, t

def getMeshMapping(xfmMappingItems, consider=None, longName=False):

    sConsiderList = mc.ls(consider, long=longName, ni=True) if consider else None
    canLog = lambda s: (not sConsiderList) or (sConsiderList and (s in sConsiderList))

    sLockedList = []
    sNoMatchList = []
    sMultiMatchList = []

    def iterSrcMeshShapes(xfmMappingItems):

        for sSrcXfm, sTrgtXfm in iterMatchedObjects(xfmMappingItems):

            sMeshShapeList = listChildMeshes(sSrcXfm, longName=longName)
            if not sMeshShapeList:
                continue

            if len(sMeshShapeList) > 1:
                pm.displayWarning("Multiple mesh shapes found under '{}'.".format(sSrcXfm))
                continue

            sSrcMeshShape = sMeshShapeList[0]

            if mc.lockNode(sSrcMeshShape, q=True, lock=True)[0]:
                if canLog(sSrcXfm):
                    pm.displayWarning("Locked node ignored: '{}'".format(sSrcMeshShape))
                    sLockedList.append(sSrcMeshShape)
                continue

            srcDagPath = myapi.getDagPath(sSrcMeshShape)
            if srcDagPath.isInstanced():
                n = srcDagPath.instanceNumber()
                if n > 0:
                    if canLog(sSrcXfm):
                        pm.displayInfo("Instanced copy number {} ignored: '{}'"
                                       .format(n, sSrcMeshShape))
                    continue

            yield sSrcXfm, sTrgtXfm, sSrcMeshShape

    mappingItems = list(iterSrcMeshShapes(xfmMappingItems))

    sSrcXfm = None
    for i, items in enumerate(mappingItems):

        sSrcXfm, sTrgtXfm, sSrcMeshShape = items
        found = None

        sMeshShapeList = listChildMeshes(sTrgtXfm, longName=longName)
        if sMeshShapeList:
            if len(sMeshShapeList) == 1:
                found = sMeshShapeList[0]
            else:
                if canLog(sSrcXfm):
                    pm.displayWarning("Multiple mesh shapes found under '{}'.".format(sTrgtXfm))
                    sMultiMatchList.append(sSrcXfm)
                found = sMeshShapeList
        elif canLog(sSrcXfm):
            pm.displayWarning("No mesh shape found under '{}'.".format(sTrgtXfm))
            sNoMatchList.append(sSrcXfm)

        mappingItems[i] = (sSrcMeshShape, found) if found else None

    if sLockedList:
        sObjSet = addLoggingSet("lockedNodes_" + getNamespace(sLockedList[0]))
        mc.sets(sLockedList, e=True, include=sObjSet)

    if sSrcXfm is not None:

        sNamespace = getNamespace(sSrcXfm)
        if sNoMatchList:
            sObjSet = addLoggingSet("noShapeMatch_" + sNamespace)
            mc.sets(sNoMatchList, e=True, include=sObjSet)

        if sMultiMatchList:
            sObjSet = addLoggingSet("multiShapesMatch_" + sNamespace)
            mc.sets(sMultiMatchList, e=True, include=sObjSet)

    return tuple(itm for itm in mappingItems if itm)

def relevantXfmAttrs(sXfm):

    flags = dict(unlocked=True, connectable=True, scalar=True)

    sAttrSet = set(listForNone(mc.listAttr(sXfm, keyable=True, **flags)))
    sAttrSet.update(listForNone(mc.listAttr(sXfm, userDefined=True, **flags)))

    return sAttrSet

def transferXfmAttrs(astToAbcXfmMap, only=None, attrs=None, discardAttrs=None, dryRun=False):

    if isinstance(astToAbcXfmMap, dict):
        astToAbcXfmItems = tuple(astToAbcXfmMap.iteritems())
    else:
        astToAbcXfmItems = astToAbcXfmMap

    sDiscardAttrSet = argToSet(discardAttrs)
    sOnlyAttrSet = argToSet(attrs)

    sLockedList = []
    sOnlyList = mc.ls(only, long=True, ni=True) if only else only

    for sAstXfm, sAbcXfm in iterMatchedObjects(astToAbcXfmItems):

        astDagPath = myapi.getDagPath(sAstXfm)
        if sOnlyList and (astDagPath.fullPathName() not in sOnlyList):
            continue

        sAbcAttrSet = relevantXfmAttrs(sAbcXfm)
        sAstAttrSet = relevantXfmAttrs(sAstXfm)

        if sOnlyAttrSet:
            sSameAttrSet = sAbcAttrSet & sAstAttrSet & sOnlyAttrSet
        else:
            sAbcAttrSet.update(iterConnectedAttrs(sAbcXfm, s=True, d=False))
            sSameAttrSet = (sAstAttrSet & sAbcAttrSet) - sDiscardAttrSet

        if not dryRun:
            for sAttr in sSameAttrSet:
                breakConnections("input", sAstXfm + "." + sAttr)

            mc.copyAttr(sAbcXfm, sAstXfm, values=True, inConnections=True,
                        keepSourceConnections=True, attribute=tuple(sSameAttrSet))

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

def meshMismatchStr(st1, st2):
    return " ".join("{}={}".format(k, v) for k, v in sorted(st1.iteritems()) if v != st2.get(k))

def transferMeshShapes(astToAbcMeshMap, only=None, dryRun=False):

    global UNUSED_TRANSFER_NODES

    if isinstance(astToAbcMeshMap, dict):
        astToAbcMeshItems = tuple(astToAbcMeshMap.iteritems())
    else:
        astToAbcMeshItems = astToAbcMeshMap

    sVertsDifferList = []
    sTopoDifferList = []
    sHasHistoryList = []

    sOnlyList = mc.ls(only, long=True, ni=True) if only else only

    for sAstMeshShape, sAbcMeshShape in iterMatchedObjects(astToAbcMeshItems):

        astMeshPath = myapi.getDagPath(sAstMeshShape)
        sAstMeshXfm = astMeshPath.fullPathName().rsplit("|", 1)[0]
        if sOnlyList and (sAstMeshXfm not in sOnlyList):
            continue

        #print sAstMeshShape, sAbcMeshShape

        if mc.listConnections(sAstMeshShape + ".inMesh", s=True, d=False):
            sHasHistoryList.append(sAstMeshShape)
            pm.displayWarning("Mesh with history ignored: '{}'".format(sAstMeshShape))
            continue

        abcMeshStat = mc.polyEvaluate(sAbcMeshShape, v=True, f=True, e=True, t=True)
        astMeshStat = mc.polyEvaluate(sAstMeshShape, v=True, f=True, e=True, t=True)

        if abcMeshStat != astMeshStat:
            if abcMeshStat["vertex"] != astMeshStat["vertex"]:
                sMsg = "Number of vertices differs:"
                sMsg += "\n    - '{}': {} verts".format(sAbcMeshShape, abcMeshStat["vertex"])
                sMsg += "\n    - '{}': {} verts".format(sAstMeshShape, astMeshStat["vertex"])
                pm.displayWarning(sMsg)
                sVertsDifferList.extend((sAbcMeshShape, sAstMeshShape))
                continue
            else:
                sMsg = "Same vertices but topology differs:"
                sMsg += ("\n    - cache mesh: {}  on '{}'"
                         .format(meshMismatchStr(abcMeshStat, astMeshStat), sAbcMeshShape))
                sMsg += ("\n    - asset mesh: {}  on '{}'"
                         .format(meshMismatchStr(astMeshStat, abcMeshStat), sAstMeshShape))
                pm.displayInfo(sMsg)
                sTopoDifferList.extend((sAbcMeshShape, sAstMeshShape))

        sAbcOutAttr = mc.listConnections(sAbcMeshShape, s=True, d=False,
                                         type="AlembicNode", plugs=True)
        bDeformedMesh = False
        if sAbcOutAttr:
            sAbcOutAttr = sAbcOutAttr[0]
            bDeformedMesh = True

        bSameVerts = False
        if not bDeformedMesh:
            bSameVerts = (mc.polyCompare(sAbcMeshShape, sAstMeshShape, vertices=True) == 0)

        if mc.referenceQuery(sAstMeshShape, isNodeReferenced=True):
            if (bDeformedMesh or (not bSameVerts)) and (not dryRun):
                sPolyTrans = mc.polyTransfer(sAstMeshShape, ao=sAbcMeshShape,
                                             uv=False, v=True, vc=False, ch=True)[0]
            if bDeformedMesh and (not dryRun):
                mc.connectAttr(sAbcOutAttr, sPolyTrans + ".otherPoly", f=True)
        elif not bSameVerts:
            srcMesh = om.MFnMesh(myapi.getDagPath(sAbcMeshShape))
            dstMesh = om.MFnMesh(astMeshPath)
            if not dryRun:
                dstMesh.setPoints(srcMesh.getPoints())

    if sHasHistoryList:
        sNmspc = getNamespace(sHasHistoryList[0])
        sObjSet = addLoggingSet("hasHistory_" + sNmspc)
        mc.sets(sHasHistoryList, e=True, include=sObjSet)

    if sVertsDifferList:
        sObjSet = addLoggingSet("VERTICES_MISMATCH")
        mc.sets(sVertsDifferList, e=True, include=sObjSet)

    if sTopoDifferList:
        sObjSet = addLoggingSet("TOPOLOGY_MISMATCH")
        mc.sets(sTopoDifferList, e=True, include=sObjSet)


def importCaches(**kwargs):

    bDryRun = kwargs.pop("dryRun", False)
    bRemoveRefs = kwargs.pop("removeRefs", False)
    bUseCacheObjset = kwargs.pop("useCacheSet", True)

    damShot = entityFromScene()
    sAbcDirPath = mop.getAlembicCacheDir(damShot)

    oAbcRefList = []

    def abort(oAbcRef):
        if bRemoveRefs and bDryRun:
            oAbcRef.remove()

    oAbcRefDct = dict(pm.listReferences(namespaces=True, references=True))

    for sAstGeoGrp in mop.iterGeoGroups(**kwargs):

        sAstNmspc = sAstGeoGrp.rsplit("|", 1)[-1].rsplit(":", 1)[0]
        sAbcNmspc = sAstNmspc + "_cache"
        sAbcPath = pathJoin(sAbcDirPath, sAbcNmspc + ".abc")

        print "\nImporting caches from '{}'".format(sAbcPath)

        if not osp.isfile(sAbcPath):
            pm.displayWarning("No such alembic file: '{}'".format(sAbcPath))
            continue

        if sAbcNmspc in oAbcRefDct:
            oAbcRef = oAbcRefDct[sAbcNmspc]
            oAbcRef.load()
            sAbcNodeList = mc.ls(sAbcNmspc + ":*")
        else:
            sAbcNodeList = mc.file(sAbcPath, type="Alembic", r=True, ns=sAbcNmspc,
                                   rnn=True, mergeNamespacesOnClash=False, gl=True)

            oAbcRef = pm.PyNode(sAbcNodeList[0]).referenceFile()
            sAbcNmspc = oAbcRef.namespace

        if not (bRemoveRefs and bDryRun):
            oAbcRefList.append(oAbcRef)
#        else:
#            mc.refresh()

        sCacheObjList = None
        if bUseCacheObjset:

            sCacheObjsetName = sAstNmspc + ":set_meshCache"
            sCacheObjset = mop.getNode(sCacheObjsetName)
            if not sCacheObjset:
                pm.displayError("Could not found '{}' !".format(sCacheObjsetName))
                abort(oAbcRef);continue

            sCacheObjList = mc.sets(sCacheObjset, q=True)
            if not sCacheObjList:
                pm.displayError("'{}' is empty !".format(sCacheObjsetName))
                abort(oAbcRef);continue

        astToAbcXfmItems = getTransformMapping(sAstGeoGrp, sAbcNmspc,
                                                consider=sCacheObjList)

        astToAbcMeshItems = getMeshMapping(astToAbcXfmItems,
                                           consider=sCacheObjList)

        transferXfmAttrs(astToAbcXfmItems, only=sCacheObjList, dryRun=bDryRun)

        #mc.refresh()

        sRefAbcNode = ""
        sFoundList = mc.ls(sAbcNodeList, type="AlembicNode")
        if sFoundList:
            #pm.displayInfo("No Alembic Node imported !")
            sRefAbcNode = sFoundList[0]

        transferMeshShapes(astToAbcMeshItems, only=sCacheObjList, dryRun=bDryRun)
        #transferXfmAttrs(astToAbcXfmItems, attrs="visibility", dryRun=bDryRun)

        if sRefAbcNode and (not bDryRun):
            sDupAbcNode = mc.duplicate(sRefAbcNode, ic=True)[0]
            transferOutConnections(sRefAbcNode, sDupAbcNode)

        abort(oAbcRef)

    mc.refresh()

    bKeepRefInLog = False

    sRefNodeSet = set()
    sLogSetName = "log_CACHE_IMPORT"
    if LOGGING_SETS:
        oObjSet = pm.sets(LOGGING_SETS, n=sLogSetName)
        if bRemoveRefs and bKeepRefInLog:
            sRefNodeSet = set(pm.referenceQuery(oObj, referenceNode=True, topReference=True)
                              for oObj in oObjSet.flattened() if oObj.isReferenced())

    if bRemoveRefs:
        if bKeepRefInLog:
            for i, oAbcRef in enumerate(oAbcRefList):
                if oAbcRef.refNode.name() not in sRefNodeSet:
                    oAbcRef.remove()
                    oAbcRefList[i] = None

            if oAbcRefList:
                print "\nReferences kept because some of their objects appear in '{}' set:".format(sLogSetName)
                for oAbcRef in oAbcRefList:
                    if oAbcRef:
                        print "    - '{}': '{}'".format(oAbcRef.refNode, oAbcRef)
        else:
            for oAbcRef in oAbcRefList:
                oAbcRef.remove()

#def processAllOrSelected(func):
#    def doIt(*args, **kwargs):
#
#
#
#    return doIt

