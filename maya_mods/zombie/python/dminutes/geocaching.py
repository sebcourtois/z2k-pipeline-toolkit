
import sys
import os
import os.path as osp
from collections import OrderedDict
from datetime import datetime
from functools import partial

import maya.api.OpenMaya as om
import maya.cmds as mc

from pymel.util.arguments import listForNone
import pymel.core as pm

from pytd.util.qtutils import setWaitCursor
from pytd.util.fsutils import pathJoin, jsonWrite, jsonRead, pathResolve, \
    pathRelativeTo
from pytd.util.sysutils import grouper, argToSet

from pytaya.util import apiutils as myapi
#from pytaya.core import system as myasys
from davos_maya.tool import reference as myaref, dependency_scan
from davos_maya.tool.general import infosFromScene, assertSceneInfoMatches

from dminutes import maya_scene_operations as mop
from pytaya.core.general import lsNodes

LOGGING_SETS = []
USE_LOGGING_SETS = True
LAUNCH_TIME = None
UNUSED_TRANSFER_NODES = []

def iterGeoGroups(**kwargs):

    bSelected = kwargs.get("selected", kwargs.get("sl", False))
    sObjList = kwargs.get("among", None)
    sNmspcList = kwargs.get("namespaces", None)

    if sObjList:
        bSelected = False

    if bSelected:
        sObjList = mc.ls(sl=True, dag=True, type="shape", ni=True)
        sNmspcList = set(o.rsplit("|", 1)[-1].rsplit(":", 1)[0] for o in sObjList)
    elif sNmspcList is None:
        sNmspcList = mc.namespaceInfo(listOnlyNamespaces=True)

    for sNmspc in sNmspcList:

        if sNmspc.endswith("_cache"):
            continue

        sGeoGrp = sNmspc + ":grp_geo"
        if mc.objExists(sGeoGrp):
            yield sGeoGrp

def withParallelEval(func):
    def doIt(*args, **kwargs):
        sEvalMode = mc.evaluationManager(q=True, mode=True)[0]
        if sEvalMode != "parallel":
            mc.evaluationManager(e=True, mode="parallel")
            mc.refresh()
        else:
            sEvalMode = ""

        try:
            res = func(*args, **kwargs)
        finally:
            if sEvalMode:
                mc.evaluationManager(e=True, mode=sEvalMode)
        return res
    return doIt

def getNamespace(sNode):
    return sNode.rsplit("|", 1)[-1].rsplit(":", 1)[0]

def iterConnectedAttrs(sNode, **kwargs):

    bSrc = kwargs.pop("source", kwargs.pop("s", True))
    bDst = kwargs.pop("destination", kwargs.pop("d", True))

    sConnList = mc.listConnections(sNode, s=bSrc, d=bDst, c=1, p=1)
    if sConnList:
        for i in xrange(0, len(sConnList), 2):
            yield sConnList[i].split(".", 1)[1]

def addLoggingSet(sBaseName, members):

    global LOGGING_SETS, USE_LOGGING_SETS, LAUNCH_TIME

    if not USE_LOGGING_SETS:
        return

    if not LAUNCH_TIME:
        LAUNCH_TIME = datetime.now()

    sDate = LAUNCH_TIME.strftime("_%Y%m%d_%Hh%M")

    sCurCnt = mc.container(q=True, current=True)
    if sCurCnt:
        mc.container(sCurCnt, e=True, current=False)

    try:
        sObjSet = mop.addNode("objectSet", "log_" + sBaseName + sDate, unique=True)
        mc.sets(members, e=True, include=sObjSet)
    finally:
        if sCurCnt:
            mc.container(sCurCnt, e=True, current=True)

    if sObjSet not in LOGGING_SETS:
        LOGGING_SETS.append(sObjSet)

    return sObjSet

def listChildMeshes(sXfm, longName=False):

    res = mc.listRelatives(sXfm, c=True, type="mesh", path=not longName, fullPath=longName)
    if not res:
        return []

    return mc.ls(res, ni=True)

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

def _confirmProcessing(sProcessLabel, **kwargs):

    bSelected = kwargs.pop("selected", None)

    if bSelected is None:

        bSelected = True
        sGeoGrpList = tuple(iterGeoGroups(selected=bSelected, **kwargs))

        sMsg = "{} caches for which assets ?".format(sProcessLabel)

        sButtonList = ['All', 'Cancel']
        if sGeoGrpList:
            sButtonList = ['All', '{} Selected'.format(len(sGeoGrpList)), 'Cancel']

        sRes = pm.confirmDialog(title='DO YOU WANT TO...',
                                message=sMsg,
                                button=sButtonList,
                                icon="question")
        if sRes == "Cancel":
            #pm.displayInfo("Canceled !")
            raise RuntimeWarning("Canceled !")
        elif sRes == 'All':
            bSelected = False
            sGeoGrpList = tuple(iterGeoGroups(selected=bSelected, **kwargs))
    else:
        sGeoGrpList = tuple(iterGeoGroups(selected=bSelected, **kwargs))

    return sGeoGrpList, bSelected

def seperatorStr(numLines, width=120, decay=20, reverse=False):
    lines = (((numLines - 1 - i) * (width - ((i + 1) * decay)) * " ").center((width - (i * decay)), "#")
             for i in xrange(numLines))
    return "\n".join(sorted((l.center(width) for l in lines), reverse=reverse))

def relevantXfmAttrs(sXfm):

    flags = dict(unlocked=True, connectable=True, scalar=True)

    sAttrSet = set(listForNone(mc.listAttr(sXfm, keyable=True, **flags)))
    sAttrSet.update(listForNone(mc.listAttr(sXfm, userDefined=True, **flags)))

    return set(at for at in sAttrSet if not (("." in at) and not mc.objExists(sXfm + "." + at)))

def exportScalarAttrs(sFilePath, sNodeList, attrs=None, discardAttrs=None,
                      addAttrs=None, dryRun=False):

    sDiscardAttrSet = argToSet(discardAttrs)

    listAttrs = lambda n: listForNone(mc.listAttr(n, scalar=True, settable=True,
                                                 visible=True, connectable=True))

    bCheckIfExists = True
    if callable(attrs):
        sOnlyAttrSet = set()
        listAttrs = attrs
        bCheckIfExists = False
    else:
        sOnlyAttrSet = argToSet(attrs)

    sAddAttrSet = argToSet(addAttrs)

    outData = OrderedDict()
    #count = len(sNodeList)
    for sNode in sNodeList:

        sAttrSet = set(listAttrs(sNode))

        if sOnlyAttrSet:
            sAttrSet &= sOnlyAttrSet

        sAttrSet -= sDiscardAttrSet
        sAttrSet.update(sAddAttrSet)

        if not sAttrSet:
            continue

        values = OrderedDict()

        for sAttr in sAttrSet:

            sNodeAttr = sNode + "." + sAttr

            if bCheckIfExists and ("." in sAttr) and not mc.objExists(sNodeAttr):
                continue

            values[sAttr] = mc.getAttr(sNodeAttr)

        outData[sNode] = values

    if not dryRun:
        jsonWrite(sFilePath, outData)

@setWaitCursor
def exportLayoutInfo(**kwargs):

    bPublish = kwargs.get("publish", False)
    bDryRun = kwargs.pop("dryRun", False)
    sComment = kwargs.pop("comment", "")

    scnInfos = infosFromScene()
    damShot = scnInfos["dam_entity"]
    privScnFile = scnInfos["rc_entry"]

    sMsg = "Layout infos can only be exported from a layout scene (of course)."
    assertSceneInfoMatches(scnInfos, "layout_scene", msg=sMsg)

    sPrivFilePath = damShot.getPath("private", "layoutInfo_file")

    sDirPath = os.path.dirname(sPrivFilePath)
    if (not os.path.exists(sDirPath)) and (not bDryRun):
        os.makedirs(sDirPath)

    sAllCrvList = mc.ls(mc.ls("*:asset", dag=True, ni=True), et="nurbsCurve", long=True)
    sCrvXfmList = tuple(s.rsplit("|", 1)[0] for s in sAllCrvList if ":tkrig|" not in s.lower())

    sXfmList = mc.ls(mc.ls("*:grp_geo", dag=True, ni=True), et="transform")
    sXfmList.extend(mc.ls(sCrvXfmList, et="transform"))
    if not sXfmList:
        pm.displayWarning("No layout info to export !")
        return

    print " Exporting layout info... ".center(100, "-")

    exportScalarAttrs(sPrivFilePath, sXfmList, attrs=relevantXfmAttrs,
                      addAttrs="worldMatrix", dryRun=bDryRun)

    res = sPrivFilePath
    if bPublish:
        if not sComment:
            sComment = "from {}".format(privScnFile.name)

        pubFile = damShot.getRcFile("public", "layoutInfo_file", weak=True)
        parentDir = pubFile.parentDir()
        res = parentDir.publishFile(sPrivFilePath, autoLock=True, autoUnlock=True,
                                    comment=sComment, dryRun=bDryRun, saveChecksum=False)
    else:
        pm.displayInfo("Layout info exported to '{}'".format(os.path.normpath(sPrivFilePath)))

    return res

ABC_PREVIOUS_FRAME = 0
ABC_PROGRESS_LINE = ""
def abcProgress(iCurFrame, iEndFrame):

    global ABC_PREVIOUS_FRAME, ABC_PROGRESS_LINE

    if iCurFrame == ABC_PREVIOUS_FRAME:
        return

    ABC_PREVIOUS_FRAME = iCurFrame
    sMsg = "{}/{}".format(iCurFrame, iEndFrame)
    if iCurFrame == iEndFrame or len(ABC_PROGRESS_LINE) >= 180:
        sMsg += "\n"
        ABC_PROGRESS_LINE = ""
    else:
        sMsg += " "

    ABC_PROGRESS_LINE += sMsg
    sys.stdout.write(sMsg)

@withParallelEval
def exportCaches(**kwargs):

    sProcessLabel = kwargs.pop("processLabel", "Export")
    bDryRun = kwargs.pop("dryRun", False)
    frameRange = kwargs.pop("frameRange", None)
    if frameRange:
        frameRange = tuple(int(f) for f in frameRange)
    bRaw = kwargs.pop("raw", False)
    bJsonOnly = kwargs.pop("jsonOnly", False)

    scnInfos = infosFromScene()
    damShot = scnInfos["dam_entity"]

    sMsg = "Caches can only be exported from an animation scene."
    assertSceneInfoMatches(scnInfos, "anim_scene", msg=sMsg)

    if not bRaw:
        myaref.loadAssetsAsResource("anim_ref", checkSyncState=True, selected=False, fail=True)

    sGeoGrpList, bSelected = _confirmProcessing(sProcessLabel, **kwargs)
    if not sGeoGrpList:
        sMsg = "No geo groups found{}".format(" from selection." if bSelected else ".")
        raise RuntimeError(sMsg)

    sCacheDirPath = mop.getMayaCacheDir(damShot).replace("\\", "/")
    if not osp.exists(sCacheDirPath):
        os.makedirs(sCacheDirPath)

    scnFrmRange = (int(pm.playbackOptions(q=True, animationStartTime=True)),
                   int(pm.playbackOptions(q=True, animationEndTime=True)))

    if not frameRange:
        pm.displayWarning("No frame range was given so, retreived from scene: {}"
                          .format(scnFrmRange))
        frameRange = scnFrmRange
    elif frameRange != scnFrmRange:
        sMsg = "Frame ranges differ:"
        sMsg += "\n    - shot : {}".format(frameRange)
        sMsg += "\n    - scene: {}".format(scnFrmRange)
        sMsg += "\nthe given range will be used."
        pm.displayWarning(sMsg)

    preRollEndFrame = frameRange[0] - 1
    preRollRange = (preRollEndFrame - 50, preRollEndFrame)

    sCurScnPath = pm.sceneName()
    sJobCmdList = []
    jobForRootDct = OrderedDict()
    sJsonPath = pathJoin(sCacheDirPath, "abcExport.json")
    if bSelected and osp.isfile(sJsonPath):
        prevExportInfos = jsonRead(sJsonPath)
        jobForRootDct = OrderedDict((j["root"], j) for j in prevExportInfos["jobs"])
    else:
        prevExportInfos = {}

    sJobOpts = "-dataFormat ogawa -noNormals -uvWrite -writeVisibility"

    sJobParts = [
    r"-root {root} -file {file}",
    r"-frameRange {frameRange[0]} {frameRange[1]}",
    r"-frameRange {preRollRange[0]} {preRollRange[1]} -preRoll",
    "{options}",
    r"-pythonPerFrameCallback '_abcProgress(int(\"#FRAME#\"),{frameRange[1]})'",
    r"-pythonPostJobCallback 'print(\"Exported \'{root}\' >> \'{file}\'\")'",
    ]
    sJobFmt = " ".join(sJobParts)

    if not bRaw:
        for sBodyResAttr in mc.ls("*.Body_res", r=True):
            print "switching", sBodyResAttr, "to High."
            if not bDryRun:
                try:
                    mc.setAttr(sBodyResAttr, 1)
                except Exception as e:
                    pm.displayWarning(e.message)

    for sGeoGrp in sGeoGrpList:

        if not mc.ls(sGeoGrp, dag=True, type="mesh"):
            pm.displayInfo("No meshes found under '{}': No geo cache to export."
                           .format(sGeoGrp))
            continue

        sAstNmspc = getNamespace(sGeoGrp)
        sAbcFilePath = pathJoin(sCacheDirPath, sAstNmspc + "_cache.abc")

        jobInfos = dict(root=sGeoGrp, file=sAbcFilePath, options=sJobOpts,
                        frameRange=frameRange, preRollRange=preRollRange,)

        sJobCmd = sJobFmt.format(**jobInfos)
        sJobCmdList.append(sJobCmd)
        if bDryRun:
            print "AbcExport: ", sJobCmd

        jobInfos["file"] = pathRelativeTo(sAbcFilePath, sCacheDirPath)
        jobInfos["source_file"] = sCurScnPath

        jobForRootDct[sGeoGrp] = jobInfos

    exportInfos = {"jobs":jobForRootDct.values()}

    if not bDryRun:
        if not bJsonOnly:
            m = sys.modules["__main__"]
            m._abcProgress = abcProgress
            mc.AbcExport(v=False, j=sJobCmdList)

        jsonWrite(sJsonPath, exportInfos)

    return exportInfos

def _iterNodePrefixedWith(sNodeList, *prefixes):
    for sNode in sNodeList:
        sPrefix = sNode.rsplit("|", 1)[-1].rsplit(":")[-1].split("_", 1)[0]
        if sPrefix in prefixes:
            yield sNode

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

    return

def meshMismatchStr(st1, st2):
    return " ".join("{}={}".format(k, v) for k, v in sorted(st1.iteritems()) if v != st2.get(k))

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
                pm.displayWarning("Missing object: '{}'".format(sTrgtDagPath))
                sNoMatchList.append(sSrcDagPath)

        mappingItems[i] = (sSrcDagPath, found)

    if sLockedList:
        addLoggingSet("lockedNodes_" + sSrcNamespace.strip(":"), sLockedList)

    if sNoMatchList:
        addLoggingSet("noObjMatch_" + sSrcNamespace.strip(":"), sNoMatchList)

    if sMultiMatchList:
        addLoggingSet("multiObjsMatch_" + sSrcNamespace.strip(":"), sMultiMatchList)

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
        addLoggingSet("lockedNodes_" + getNamespace(sLockedList[0]), sLockedList)

    if sSrcXfm is not None:

        sNamespace = getNamespace(sSrcXfm)
        if sNoMatchList:
            addLoggingSet("noShapeMatch_" + sNamespace, sNoMatchList)

        if sMultiMatchList:
            addLoggingSet("multiShapesMatch_" + sNamespace, sMultiMatchList)

    return tuple(itm for itm in mappingItems if itm)

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
        addLoggingSet("lockedNodes_" + sNmspc, sLockedList)

    return True

def transferVisibilities(astToAbcXfmMap, dryRun=False):

    if isinstance(astToAbcXfmMap, dict):
        astToAbcXfmItems = tuple(astToAbcXfmMap.iteritems())
    else:
        astToAbcXfmItems = astToAbcXfmMap

    sAttr = "visibility"

    sHiddenList = []
    sShowedList = []

    for sAstXfm, sAbcXfm in iterMatchedObjects(astToAbcXfmItems):

        sAbcVizAttr = sAbcXfm + "." + sAttr
        sAstVizAttr = sAstXfm + "." + sAttr

        bAbcViz = mc.getAttr(sAbcVizAttr)
        bAstViz = mc.getAttr(sAstVizAttr)

        if bAstViz == bAbcViz:
            continue

        if bAstViz:
            sHiddenList.append(sAstXfm)
            sMsg = "CACHE HIDE: '{}'".format(sAstXfm)
        else:
            sShowedList.append(sAstXfm)
            sMsg = "CACHE SHOW: '{}'".format(sAstXfm)

        print sMsg

        try:
            if not dryRun:
                mc.setAttr(sAstVizAttr, bAbcViz)
        except RuntimeError as e:
            sMsg = e.message.strip()
            if "locked or connected" in sMsg:
                pm.displayWarning(sMsg)
            else:
                raise

    if sHiddenList:
        sNmspc = getNamespace(sHiddenList[0])
        addLoggingSet("hidden_" + sNmspc, sHiddenList)

    if sShowedList:
        sNmspc = getNamespace(sShowedList[0])
        addLoggingSet("showed_" + sNmspc, sShowedList)

def transferMeshShapes(astToAbcMeshMap, only=None, dryRun=False):

    global UNUSED_TRANSFER_NODES

    if isinstance(astToAbcMeshMap, dict):
        astToAbcMeshItems = tuple(astToAbcMeshMap.iteritems())
    else:
        astToAbcMeshItems = astToAbcMeshMap

    sVertsDifferList = []
    sTopoDifferList = []
    sHasHistoryList = []

    sOnlyList = mc.ls(only, long=True, ni=True) if only else None

    for sAstMeshShape, sAbcMeshShape in iterMatchedObjects(astToAbcMeshItems):

        astMeshPath = myapi.getDagPath(sAstMeshShape)
        sAstMeshXfm = astMeshPath.fullPathName().rsplit("|", 1)[0]
        if sOnlyList and (sAstMeshXfm not in sOnlyList):
            continue

        #print sAstMeshShape, sAbcMeshShape

        sConnecList = mc.listHistory(sAstMeshShape, il=2, pdo=True)
        if sConnecList:
            sConnecList = lsNodes(sConnecList, nodeNames=True, not_rn=True)
            #print sAstMeshShape, sConnecList
            if sConnecList:
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
        addLoggingSet("hasHistory_" + sNmspc, sHasHistoryList)

    if sVertsDifferList:
        addLoggingSet("VERTICES_MISMATCH", sVertsDifferList)

    if sTopoDifferList:
        addLoggingSet("TOPOLOGY_MISMATCH", sTopoDifferList)

def transferOutConnections(sSrcNode, sDstNode, useNamespace=True):

    sConnectList = mc.listConnections(sSrcNode, s=False, d=True, c=True, p=True,
                                      skipConversionNodes=True)
    if not sConnectList:
        return

    sSrcNmspc = getNamespace(sSrcNode)

    sConnectList = tuple((s.split(".", 1)[-1], d) for s, d in grouper(2, sConnectList))
    for sSrcAttr, sDstPlug in sConnectList:
        if useNamespace and sSrcNmspc == getNamespace(sDstPlug.rsplit('.', 1)[0]):
            continue
        mc.connectAttr(sDstNode + "." + sSrcAttr, sDstPlug, force=True)

def importLayoutVisibilities(damShot=None, onNamespaces=None, dryRun=False):

    if not damShot:
        damShot = infosFromScene()["dam_entity"]

    layoutInfoFile = damShot.getRcFile("public", "layoutInfo_file", fail=True)
    layoutData = jsonRead(layoutInfoFile.absPath())

    print "\n" + " Importing Layout visibilities ".center(120, "-")

    for sObj, values in layoutData.iteritems():

        if onNamespaces and (getNamespace(sObj) not in onNamespaces):
            continue

        if not mc.objExists(sObj):
            continue

        for sAttr, v in values.iteritems():

            if "visibility" not in sAttr.lower():
                continue

            sObjAttr = sObj + "." + sAttr

            if not mc.objExists(sObjAttr):
                pm.displayInfo("No such attribute: {}".format(sObjAttr))

            bObjViz = mc.getAttr(sObjAttr)
            if bObjViz == v:
                continue

            try:
                if not dryRun:
                    mc.setAttr(sObjAttr, v)
            except RuntimeError as e:
                if "locked or connected" in e.message:
                    pass
                else:
                    raise#pm.displayWarning(e.message.strip())

            if sAttr == "visibility":
                if bObjViz:
                    sMsg = "LAYOUT HIDE: '{}'".format(sObj)
                else:
                    sMsg = "LAYOUT SHOW: '{}'".format(sObj)
            else:
                if bObjViz:
                    sMsg = "LAYOUT HIDE: '{}'".format(sObjAttr)
                else:
                    sMsg = "LAYOUT SHOW: '{}'".format(sObjAttr)

            print sMsg

    print " Layout visibilities imported ".center(120, "-") + "\n"

def cleanImportContext(func):
    def doIt(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        finally:
            sCurCntnr = mc.container(q=True, current=True)
            if sCurCntnr:
                mc.container(sCurCntnr, e=True, current=False)
        return res
    return doIt

def importCaches(sSpace, **kwargs):

    global LOGGING_SETS, USE_LOGGING_SETS, LAUNCH_TIME

    bDryRun = kwargs.pop("dryRun", False)
    bRemoveRefs = kwargs.pop("removeRefs", True)
    bUseCacheObjset = kwargs.pop("useCacheSet", True)
    #bForce = kwargs.pop("force", False)

    sepWidth = 120
    def doneWith(oAbcRef, remove=True, container=None):
        if bRemoveRefs and remove:# and bDryRun:
            oAbcRef.remove()

    scnInfos = infosFromScene()
    damShot = scnInfos["dam_entity"]

    if not bDryRun:
        sMsg = "Caches can only be imported onto a final layout scene."
        assertSceneInfoMatches(scnInfos, "finalLayout_scene", msg=sMsg)

    if sSpace == "local":
        sCacheDirPath = mop.getMayaCacheDir(damShot)
    elif sSpace in ("public", "private"):
        sCacheDirPath = damShot.getPath(sSpace, "finalLayoutCache_dir")
    else:
        raise ValueError("Invalid space argument: '{}'".format(sSpace))

    if not osp.isdir(sCacheDirPath):
        raise EnvironmentError("Could not found caches directory: '{}'".format(sCacheDirPath))

    exportInfos = jsonRead(pathJoin(sCacheDirPath, "abcExport.json"))
    exportJobList = exportInfos["jobs"]

    sProcessLabel = kwargs.pop("processLabel", "Import")
    bCheckAstExists = False
    sGeoGrpList, bSelected = _confirmProcessing(sProcessLabel, **kwargs)
    if not bSelected:
        sGeoGrpList = tuple(j["root"] for j in exportJobList)
        bCheckAstExists = True
    elif not sGeoGrpList:
        sMsg = "No geo groups found{}".format(" from selection.")
        raise RuntimeError(sMsg)
    else:
        exportJobList = tuple(j for j in exportJobList if j["root"] in sGeoGrpList)

    for jobInfos in exportJobList:
        sFilePath = jobInfos["file"]
        if not osp.isabs(sFilePath):
            jobInfos["file"] = pathJoin(sCacheDirPath, sFilePath)

#    if not exportJobList:
#        return False

    sAbcPathList = list(j["file"] for j in exportJobList)
    scanFunc = partial(scanCachesToImport, sAbcPathList)
    scanDct = dependency_scan.launch(scnInfos, scanFunc=scanFunc,
                                     modal=True,
                                     okLabel=sProcessLabel,
                                     expandTree=True,
                                     forceDialog=False)
    if scanDct is None:
        pm.displayInfo("Canceled !")
        return

    oFileRefDct = dict(pm.listReferences(namespaces=True, references=True))
    sScnNmspcList = mc.namespaceInfo(listOnlyNamespaces=True)

    pm.mel.ScriptEditor()
    pm.mel.handleScriptEditorAction("maximizeHistory")

    bRefOnly = (sProcessLabel.lower() == "reference")

    if (not bRefOnly) and (not bDryRun):

        for jobInfos in exportJobList:

            sAstGeoGrp = jobInfos["root"]

            sAstNmspc = getNamespace(sAstGeoGrp)
            sAbcNmspc = sAstNmspc + "_cache"
            sScnAbcNodeName = sAbcNmspc + "_AlembicNode"

            sAstMeshList = mc.ls(sAstNmspc + ":*", type="mesh", ni=True)
            sToDelList = []
            for sAstMesh in sAstMeshList:
                sHistList = listForNone(mc.listHistory(sAstMesh, il=2, pdo=True))
                if not sHistList:
                    continue
                sHistList = mc.ls(sHistList, type="polyTransfer")
                if sHistList:
                    sToDelList.extend(sHistList)

            if sToDelList:
                print ("delete {} 'polyTransfer' nodes on '{}'"
                       .format(len(sToDelList), sAstNmspc))
                mc.delete(sToDelList)

            sScnAbcNode = mop.getNode(sScnAbcNodeName)
            if sScnAbcNode:
                mc.delete(sScnAbcNode)

    sNmspcList = None
    if bSelected:
        sNmspcList = tuple(getNamespace(s) for s in sGeoGrpList)
    importLayoutVisibilities(damShot, onNamespaces=sNmspcList, dryRun=bDryRun)

    mc.refresh()

    print  r"""
   ______           __            ____                           __     _____ __             __           __
  / ____/___ ______/ /_  ___     /  _/___ ___  ____  ____  _____/ /_   / ___// /_____ ______/ /____  ____/ /
 / /   / __ `/ ___/ __ \/ _ \    / // __ `__ \/ __ \/ __ \/ ___/ __/   \__ \/ __/ __ `/ ___/ __/ _ \/ __  / 
/ /___/ /_/ / /__/ / / /  __/  _/ // / / / / / /_/ / /_/ / /  / /_    ___/ / /_/ /_/ / /  / /_/  __/ /_/ /  
\____/\__,_/\___/_/ /_/\___/  /___/_/ /_/ /_/ .___/\____/_/   \__/   /____/\__/\__,_/_/   \__/\___/\__,_/   
                                           /_/                                                                                                                                                                               
""".rstrip()

    for jobInfos in exportJobList:

        sAstGeoGrp = jobInfos["root"]
        sAbcFilePath = jobInfos["file"]

        sAstNmspc = getNamespace(sAstGeoGrp)
        sAbcNmspc = sAstNmspc + "_cache"
        sScnAbcNodeName = sAbcNmspc + "_AlembicNode"

        print ("\n" + (" " + sAstNmspc + " ").center(sepWidth, "-"))

        if not osp.isfile(sAbcFilePath):
            pm.displayWarning("No such alembic file: '{}'".format(sAbcFilePath))
            continue

        oAbcRef = None
        bRemRef = True
        if sAbcNmspc in oFileRefDct:
            oAbcRef = oFileRefDct[sAbcNmspc]
            if osp.normcase((oAbcRef.path)) == osp.normcase(sAbcFilePath):
                print "Reloading cache reference: '{}'".format(sAbcFilePath)
                oAbcRef.load()
                sAbcNodeList = mc.ls(sAbcNmspc + ":*")
                bRemRef = False
            else:
                oAbcRef = None

        if not oAbcRef:
            print "Importing cache file: '{}'".format(sAbcFilePath)
            sAbcNodeList = mc.file(sAbcFilePath, type="Alembic", r=True, ns=sAbcNmspc,
                                   rnn=True, mergeNamespacesOnClash=False, gl=True)

            oAbcRef = pm.PyNode(sAbcNodeList[0]).referenceFile()
            sAbcNmspc = oAbcRef.namespace

        if bRefOnly:
            doneWith(oAbcRef, bRemRef);continue

        if bCheckAstExists and sAstNmspc not in sScnNmspcList:
            pm.displayWarning("Asset NOT found: '{}'.".format(sAstNmspc))
            doneWith(oAbcRef, bRemRef);continue

        sCacheObjList = None
        if bUseCacheObjset:

            sCacheSetName = sAstNmspc + ":set_meshCache"
            sCacheObjset = mop.getNode(sCacheSetName)
            if not sCacheObjset:
                pm.displayError("Could not found '{}' !".format(sCacheSetName))
                doneWith(oAbcRef, bRemRef);continue

            sCacheObjList = mc.sets(sCacheObjset, q=True)
            if not sCacheObjList:
                pm.displayError("'{}' is empty !".format(sCacheSetName))
                doneWith(oAbcRef, bRemRef);continue

        astToAbcXfmItems = getTransformMapping(sAstGeoGrp, sAbcNmspc, longName=False,
                                               consider=sCacheObjList)

        astToAbcMeshItems = getMeshMapping(astToAbcXfmItems, longName=False,
                                           consider=sCacheObjList)

        transferXfmAttrs(astToAbcXfmItems, only=sCacheObjList, dryRun=bDryRun,
                         discardAttrs="visibility")
        try:
            transferMeshShapes(astToAbcMeshItems, only=sCacheObjList, dryRun=bDryRun)
        finally:
            if sAstNmspc in oFileRefDct:
                for sNodeName in lsNodes(sAstNmspc + ":*", not_rn=True, nodeNames=True):
                    mc.rename(sNodeName, sNodeName.rsplit(":", 1)[-1])

        transferVisibilities(astToAbcXfmItems, dryRun=bDryRun)

        if not bDryRun:
            sFoundList = mc.ls(sAbcNodeList, type="AlembicNode")
            if sFoundList:
                sRefAbcNode = sFoundList[0]
                sScnAbcNode = mc.duplicate(sRefAbcNode, ic=True)[0]
                transferOutConnections(sRefAbcNode, sScnAbcNode)
            else:
                sScnAbcNode = mc.createNode("AlembicNode", n=sScnAbcNodeName)
                mc.setAttr(sScnAbcNode + ".abc_File", sAbcFilePath, type="string")
                sAstGrp = sAstGeoGrp.replace(":grp_geo", ":asset")
                sParentList = mc.listRelatives(sAstGrp, parent=True, path=True)
                sParent = sParentList[0] if sParentList else None
                sAbcHook = mop.addNode("transform", "hook_" + sAbcNmspc,
                                       parent=sParent, unique=True)
                mc.connectAttr(sScnAbcNode + ".transOp[0]", sAbcHook + ".translateX", f=True)

        doneWith(oAbcRef, bRemRef)

    print r"""
   ______           __            ____                           __     ____                 
  / ____/___ ______/ /_  ___     /  _/___ ___  ____  ____  _____/ /_   / __ \____  ____  ___ 
 / /   / __ `/ ___/ __ \/ _ \    / // __ `__ \/ __ \/ __ \/ ___/ __/  / / / / __ \/ __ \/ _ \
/ /___/ /_/ / /__/ / / /  __/  _/ // / / / / / /_/ / /_/ / /  / /_   / /_/ / /_/ / / / /  __/
\____/\__,_/\___/_/ /_/\___/  /___/_/ /_/ /_/ .___/\____/_/   \__/  /_____/\____/_/ /_/\___/ 
                                           /_/                                                                                                                                      
""".rstrip()

    mc.refresh()

    if LOGGING_SETS:
        addLoggingSet("CACHE_IMPORT", LOGGING_SETS)

    return True

def removeCacheReferences():

    sLogSetList = mc.ls("log_*", type="objectSet")
    if sLogSetList:
        mc.delete(sLogSetList)

    for oFileRef in pm.listReferences():
        if oFileRef.path.basename().lower().endswith("_cache.abc"):
            print "removing cache", repr(oFileRef)
            oFileRef.remove()


OLDER_FILE_MSG = """
current file: {} - {}
public file  : {} - {}
""".strip()

@setWaitCursor
def scanCachesToImport(sSrcFilePathList, scnInfos=None, depConfDct=None):

    if not scnInfos:
        scnInfos = infosFromScene()

    damEntity = scnInfos["dam_entity"]
#    proj = scnInfos["project"]
#    pubLib = damEntity.getLibrary("public")

    sDepType = "geoCache_dep"
    if not depConfDct:
        depConfDct = damEntity.getDependencyConf(sDepType, scnInfos["resource"])
    pubDepDir = depConfDct["public_loc"]

#    sPubDepDirPath = pubDepDir.absPath()
#    if pubDepDir.exists():
#        pubDepDir.loadChildDbNodes(noVersions=True)

    scanResults = []

    sAllSeveritySet = set()

    def addResult(res):
        scanResults.append(res)
        sAllSeveritySet.update(res["scan_log"].iterkeys())

    for sSrcFilePath in sSrcFilePathList:

        scanLogDct = {}

        bExists = osp.isfile(sSrcFilePath)

        resultDct = {"dependency_type":sDepType,
                     "abs_path":sSrcFilePath,
                     "scan_log":scanLogDct,
                     "file_nodes":[],
                     "fellow_paths":[],
                     "publishable":False,
                     "drc_file":None,
                     "exists":bExists,
                     "public_file":None,
                    }

        _, sDepFilename = osp.split(sSrcFilePath)

        if not bExists:
            scanLogDct.setdefault("warning", []).append(('FileNotFound', sSrcFilePath))
            addResult(resultDct); continue

        pubFile = pubDepDir.getChildFile(sDepFilename, weak=True, dbNode=False)
        sPubFilePath = pubFile.absPath()
        if pubFile.exists():

            srcFileTime = datetime.fromtimestamp(osp.getmtime(sSrcFilePath))
            pubFileTime = datetime.fromtimestamp(osp.getmtime(sPubFilePath))

            if srcFileTime < pubFileTime:
                #sMsg = """File is older than its public file: \n    '{}'"""
                sMsg = OLDER_FILE_MSG.format(srcFileTime.strftime("%Y-%m-%d %H:%M"),
                                             osp.dirname(osp.normpath(sSrcFilePath)),
                                             pubFileTime.strftime("%Y-%m-%d %H:%M"),
                                             osp.dirname(osp.normpath(sPubFilePath)))

                scanLogDct.setdefault("warning", []).append(("OlderLocalFile", sMsg))

        addResult(resultDct)

    if scanResults:
        scanResults[-1]["scan_severities"] = sAllSeveritySet
        scanResults[-1]["publish_count"] = 0

    return {sDepType:scanResults}
