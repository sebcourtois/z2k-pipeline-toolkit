
#import os.path as osp
from functools import partial
from itertools import izip

from PySide import QtGui, QtCore

import maya.cmds as mc
import pymel.core as pm
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from pytd.util.fsutils import pathResolve, normCase
from pytd.util.sysutils import toStr
#from pytd.gui.dialogs import confirmDialog

from pytaya.util.sysutils import withSelectionRestored
from pytaya.core.reference import processSelectedReferences
from pytaya.core.reference import listReferences

from davos_maya.tool.general import entityFromScene, projectFromScene
#from davos_maya.tool.general import infosFromScene, listRelatedAssets

from dminutes.shotconformation import removeRefEditByAttr
from davos.core.drctypes import DrcEntry

@processSelectedReferences
def listMayaRcForSelectedRefs(oFileRef, proj, **kwargs):

    sRefPath = pathResolve(oFileRef.path)
    astLib = proj.getLibrary("public", "asset_lib")
    asset = proj.entityFromPath(sRefPath, fail=False, library=astLib)

    resultList = kwargs.pop("processResults")

    mayaRcDct = dict()
    if asset:
        mayaRcDct = dict(asset.iterMayaRcItems(**kwargs))
    res = (asset, mayaRcDct)
    resultList.append(res)

@withSelectionRestored
def switchSelectedReferences(dryRun=False, cleanEdits=False, **kwargs):

    scnEntity = entityFromScene()
    proj = scnEntity.project

    kwargs.update(confirm=False, allIfNoSelection=True, topReference=True)
    oSelRefList, assetRcList = listMayaRcForSelectedRefs(proj, **kwargs)

    assetList = tuple(ast for ast, _ in assetRcList if ast)
    if not assetList:
        pm.displayWarning("No Asset References selected !")
        return

    sRcNameSet = set()
    for _, rcDct in assetRcList:
        sRcNameSet.update(rcDct.iterkeys())

    if not sRcNameSet:
        pm.displayWarning("No available resources on which to switch !")

    sortedRcNames = sorted(sRcNameSet)

    numRefs = len(oSelRefList)
    sMsg = 'Switch {} Asset References to...'.format(numRefs)
    sChosenRcName = pm.confirmDialog(title="Hey, mon ami !",
                                     message=sMsg,
                                     button=sortedRcNames + ['Cancel'],
                                     defaultButton='Cancel',
                                     cancelButton='Cancel',
                                     dismissString='Cancel',
                                     icon="question")

    if sChosenRcName == 'Cancel':
        pm.warning("Canceled !")
        return

    i = 0
    swicthItems = []
    nonSwitchedRefList = []
    for oFileRef, assetRc in izip(oSelRefList, assetRcList):

        asset = assetRc[0]
        rcDct = assetRc[1]

        sRefPath = pathResolve(oFileRef.path)

        i += 1
        print "Checking {}/{}: '{}' ...".format(i, numRefs, oFileRef.refNode.name())

        if not asset:
            sMsg = "Unknown asset: '{}'".format(oFileRef.path)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if not oFileRef.isLoaded():
            sMsg = "Reference not loaded"
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        sRcPath = rcDct.get(sChosenRcName)
        if not sRcPath:
            sMsg = "{} has no such resource file: '{}'".format(asset, sChosenRcName)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if normCase(sRcPath) == normCase(sRefPath):
            sMsg = "Reference already switched to '{}'".format(sChosenRcName)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        mrcFile = proj.entryFromPath(sRcPath, library=asset.getLibrary(), dbNode=False)
        if not mrcFile:
            sMsg = "File not found: '{}'".format(sRcPath)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        cachedDbNode = mrcFile.loadDbNode(fromDb=False)
        if cachedDbNode:
            mrcFile.refresh(simple=True)
        else:
            mrcFile.loadDbNode(fromCache=False)

        if not mrcFile.currentVersion:
            sMsg = "No version created yet: '{}'".format(sRcPath)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        try:
            mrcFile.assertUpToDate(refresh=False)
        except AssertionError as e:
            sMsg = "File is out of sync: '{}'. {}".format(sRcPath, e.message)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        swicthItems.append((oFileRef, mrcFile))

    oFileRefList = tuple(r for r, _ in swicthItems)
    numOkRefs = len(swicthItems)
    if not dryRun:

        for i, oFileRef in enumerate(oFileRefList):
            print "Unloading {}/{}: '{}' ...".format(i + 1, numOkRefs, oFileRef.refNode.name())
            oFileRef.unload()

        if cleanEdits:
            for i, oFileRef in enumerate(oFileRefList):
                    print "Cleaning edits on {}/{}: '{}' ...".format(i + 1, numOkRefs, oFileRef.refNode.name())
                    oFileRef.clean()
        else:
            sAttrList = ("smoothDrawType", "displaySmoothMesh", "dispResolution")
            removeRefEditByAttr(attr=sAttrList, GUI=False)

        mc.refresh()

        for i, (oFileRef, mrcFile) in enumerate(swicthItems):
            #oFileRef, mrcFile = items
            print "Switching {}/{}: '{}' ...".format(i + 1, numOkRefs, oFileRef.refNode.name())
            try:
                oFileRef.load(mrcFile.envPath())
            except Exception as e:
                sMsg = toStr(e)
                nonSwitchedRefList.append((oFileRef, sMsg))
                print sMsg
                continue

    if nonSwitchedRefList:

        w = len(max((r.refNode.name() for r, _ in nonSwitchedRefList), key=len))
        def fmt(r, m):
            return "{0:<{2}}: {1}".format(r.refNode.name(), m, w)

        numFailure = len(nonSwitchedRefList)
        sSep = "\n- "
        sMsgHeader = " Failed to switch {}/{} references. ".format(numFailure, numRefs)
        sMsgBody = sSep.join(fmt(r, m) for r, m in nonSwitchedRefList)
        sMsgEnd = "".center(100, "-")

        sMsg = '\n' + sMsgHeader.center(100, "-") + sSep + sMsgBody + '\n' + sMsgEnd
        print sMsg
        pm.displayWarning(sMsgHeader + "More details in Script Editor ----" + (70 * ">"))

        #pm.mel.ScriptEditor()
    else:
        pm.displayInfo("Successfully switched {} references as '{}'"
                          .format(numRefs, sChosenRcName))


DEFAULT_FILE_ATTR = "defaultAssetFile"

def setDefaultAssetFileForSelectedRefs(assetFile="NoInput", **kwargs):

    damEntity = entityFromScene()
    proj = damEntity.project

    kwargs.update(confirm=False, allIfNoSelection=False, topReference=True, locked=False)
    oSelRefList, assetRcList = listMayaRcForSelectedRefs(proj,
                                                         filter="previz_ref",
                                                         **kwargs)

    assetList = tuple(ast for ast, _ in assetRcList if ast)
    if not assetList:
        #pm.displayWarning("No Asset References selected !")
        return

    sRcNameSet = set()
    for _, rcDct in assetRcList:
        sRcNameSet.update(rcDct.iterkeys())

    if not sRcNameSet:
        pm.displayWarning("No available resources on which to switch !")

    sAstRcName = None

    sortedRcNames = sorted(sRcNameSet)
    allowedValues = sortedRcNames + ["offloaded", ""]
    if assetFile != "NoInput":
        if assetFile not in allowedValues:
            raise ValueError("Bad value for 'assetFile' kwarg: '{}'. Are valid: {}"
                             .format(assetFile, allowedValues))
        sAstRcName = assetFile
        sChoiceList = ["OK"]
    else:
        sChoiceList = sortedRcNames + ["offloaded", "Clear"]

    numRefs = len(oSelRefList)
    if sAstRcName is None:
        sMsg = "Set default asset file for {} references to...".format(numRefs)
    else:
        sMsg = ("Set default asset file for {} references to '{}'"
                .format(numRefs, sAstRcName))

    sChoice = pm.confirmDialog(title="Hey, mon ami !",
                               message=sMsg,
                               button=sChoiceList + ["Cancel"],
                               defaultButton='Cancel',
                               cancelButton='Cancel',
                               dismissString='Cancel',
                               icon="question")

    if sChoice == "Cancel":
        pm.displayWarning("Canceled !")
        return
    elif sChoice == "Clear":
        sAstRcName = ""
    elif sAstRcName is None:
        sAstRcName = sChoice

    for oFileRef, assetRc in izip(oSelRefList, assetRcList):

        asset = assetRc[0]
        if not asset:
            continue

        oRefNode = oFileRef.refNode

        bHasAttr = oRefNode.hasAttr(DEFAULT_FILE_ATTR)
        bAddAttr = True if sAstRcName and (not bHasAttr) else False

        if bAddAttr:
            pm.lockNode(oRefNode, lock=False)
            try:
                oRefNode.addAttr(DEFAULT_FILE_ATTR, dt="string", k=False, r=True, w=True, s=True)
                bHasAttr = True
            finally:
                pm.lockNode(oRefNode, lock=True)

        if bHasAttr:
            print "set {}.{} to '{}'".format(oRefNode, DEFAULT_FILE_ATTR, sAstRcName)
            oRefNode.setAttr(DEFAULT_FILE_ATTR, sAstRcName)

@processSelectedReferences
def _loadAssetRefsToDefaultFile(oFileRef, astLib, logData, dryRun=False, **kwargs):

    oAstFileRefList = kwargs.pop("processResults")
    def loadRef(p=None):
        if not dryRun:
            oFileRef.load(p)
        logData["loaded"] += 1

    proj = astLib.project
    logItems = logData["log"]

    oRefNode = oFileRef.refNode

    sDefaultRcName = ""
    if oRefNode.hasAttr(DEFAULT_FILE_ATTR):
        sDefaultRcName = oRefNode.getAttr(DEFAULT_FILE_ATTR)

        # now only "offloaded" tag is considered.
        if sDefaultRcName != "offloaded":
            sDefaultRcName = ""

    bLoaded = oFileRef.isLoaded()
    sRefNode = oRefNode.name()

    sRefPath = pathResolve(oFileRef.path)

    ctxData = {}
    try:
        ctxData = proj.contextFromPath(sRefPath, library=astLib)
        damAst = proj._entityFromContext(ctxData, fail=True)
    except Exception as e:
        pm.displayWarning(toStr(e))
        return

#    try:
#        damAst = proj._entityFromContext(ctxData, fail=True)
#    except Exception as e:
#        logItems.append((sRefNode, "FAILED: " + toStr(e)))
#        logData["failed"] += 1
#        return

    oAstFileRefList.append(oFileRef)

    if sDefaultRcName == "offloaded":
        sMsg = "offloaded"
        if bLoaded:
            if not dryRun:
                oFileRef.unload()
        else:
            sMsg = "kept " + sMsg
        logItems.append((sRefNode, sMsg))
        return

    sCurRcName = ctxData.get("resource", "")
    sAstType = damAst.assetType
    if sAstType in ("chr", "prp", "vhl") and sCurRcName != "anim_ref":
        sDefaultRcName = "anim_ref"
        sMsg = ("a '{}' should be loaded as '{}', not '{}'..."
                .format(sAstType, sDefaultRcName, sCurRcName))
        logItems.append((sRefNode, sMsg))

    if sDefaultRcName in (sCurRcName, ""):
        sMsg = "loaded as '{}'".format(sDefaultRcName) if sDefaultRcName else "loaded"
        if not bLoaded:
            loadRef()
        else:
            sMsg = "already " + sMsg
        logItems.append((sRefNode, sMsg))
        return

    try:
        astFile = damAst.getResource("public", sDefaultRcName,
                                     dbNode=False, fail=True)
    except Exception as e:
        logItems.append((sRefNode, "FAILED: " + toStr(e)))
        logData["failed"] += 1
        return

    logItems.append((sRefNode, "switched to '{}'".format(sDefaultRcName)))
    loadRef(astFile.envPath())

def loadAssetRefsToDefaultFile(project=None, dryRun=False, selected=False):

    proj = project
    if not proj:
        proj = projectFromScene()

    astLib = proj.getLibrary("public", "asset_lib")

    logItems = []
    logData = dict(log=logItems, failed=0, loaded=0)

    _, oAstFileRefList = _loadAssetRefsToDefaultFile(astLib, logData,
                                                     dryRun=dryRun,
                                                     confirm=True,
                                                     allIfNoSelection=True,
                                                     topReference=True,
                                                     locked=False,
                                                     selected=selected)
    numFailure = logData["failed"]
    numLoaded = logData["loaded"]

    numRefs = len(oAstFileRefList)
    w = len(max((r for r, _ in logItems), key=len)) if logItems else 0
    fmt = lambda rn, m: "{0:<{2}}: {1}".format(rn, m, w)

    sSep = "\n- "
    if numFailure:
        sMsgHeader = " Failed to load {}/{} asset refs. ".format(numFailure, numRefs)
        displayFunc = pm.displayError
    else:
        sMsgHeader = " {}/{} asset refs loaded. ".format(numLoaded, numRefs)
        displayFunc = pm.displayInfo

    sMsgBody = sSep.join(fmt(r, m) for r, m in logItems)
    sMsgEnd = "".center(100, "-")

    sMsg = '\n' + sMsgHeader.center(100, "-") + sSep + sMsgBody + '\n' + sMsgEnd
    print sMsg
    displayFunc(sMsgHeader + "More details in Script Editor ----" + (70 * ">"))

    return oAstFileRefList

@processSelectedReferences
def _loadAssetsAsResource(oFileRef, sRcName, astLib, logData,
                          dryRun=False, checkSyncState=False, **kwargs):

    oAstFileRefList = kwargs.pop("processResults")
    def loadRef(p=None):
        if not dryRun:
            oFileRef.load(p)
        logData["loaded"] += 1

    proj = astLib.project
    logItems = logData["log"]

    oRefNode = oFileRef.refNode

    bLoaded = oFileRef.isLoaded()
    sRefNode = oRefNode.name()

    sRefPath = pathResolve(oFileRef.path)

    ctxData = {}
    try:
        ctxData = proj.contextFromPath(sRefPath, library=astLib)
    except Exception as e:
        pm.displayWarning(toStr(e))

    try:
        damAst = proj._entityFromContext(ctxData, fail=True)
    except Exception as e:
        logItems.append((sRefNode, "WARNING: " + toStr(e)))
        #logData["failed"] += 1
        return

    oAstFileRefList.append(oFileRef)
    curRcFile = ctxData["rc_entry"]

    try:
        rcFile = damAst.getResource("public", sRcName,
                                     dbNode=False, fail=True)
    except Exception as e:
        logItems.append((sRefNode, "WARNING: " + toStr(e)))
        #logData["failed"] += 1
        return

    sCurRcName = ctxData.get("resource", "")
    bSameRc = (sRcName == sCurRcName)
    sSeverity = "error"

    if checkSyncState:

        if bSameRc and curRcFile.isVersionFile():
            sSeverity = "warning"

        cachedDbNode = rcFile.loadDbNode(fromDb=False)
        if cachedDbNode:
            pass#rcFile.refresh(simple=True)
        else:
            rcFile.loadDbNode(fromCache=False)

        if not rcFile.currentVersion:
            logItems.append((sRefNode, "{}: " + "No version yet".format(sSeverity.upper())))
            if sSeverity == "error":
                logData["failed"] += 1
            return

        try:
            rcFile.assertUpToDate(refresh=False)
        except AssertionError as e:
            logItems.append((sRefNode, "{}: ".format(sSeverity.upper()) + toStr(e)))
            if sSeverity == "error":
                logData["failed"] += 1
            return

    if bSameRc:
        sMsg = "loaded as '{}'".format(sRcName) if sRcName else "loaded"
        if not bLoaded:
            loadRef()
        else:
            sMsg = "already " + sMsg
        logItems.append((sRefNode, sMsg))
        return

    logItems.append((sRefNode, "switched to '{}'".format(sRcName)))
    loadRef(rcFile.envPath())


def loadAssetsAsResource(sRcName, fail=False, checkSyncState=False,
                         selected=False, project=None, dryRun=False):
    proj = project
    if not proj:
        proj = projectFromScene()

    bBatchMode = mc.about(batch=True)

    astLib = proj.getLibrary("public", "asset_lib")

    logItems = []
    logData = dict(log=logItems, failed=0, loaded=0)

    if checkSyncState:
        rcFileList = []
        sAstList = []
        sRefPathSet = set(pathResolve(oFileRef.path) for oFileRef in pm.iterReferences())
        for sRefPath in sRefPathSet:
            damAst = proj.entityFromPath(sRefPath, fail=False, library=astLib)
            if not damAst:
                continue
            elif damAst.name in sAstList:
                continue
            sAstList.append(damAst.name)
            rcFile = damAst.getRcFile("public", sRcName, dbNode=False, weak=True, fail=False)
            if rcFile:
                rcFileList.append(rcFile)

        dbNodeList = proj.dbNodesFromEntries(rcFileList)
        for rcFile, dbNode in izip(rcFileList, dbNodeList):
            if not dbNode:
                rcFile.loadDbNode(fromCache=False)

    _, oAstFileRefList = _loadAssetsAsResource(sRcName, astLib, logData,
                                               confirm=True,
                                               allIfNoSelection=True,
                                               topReference=True,
                                               locked=False,
                                               selected=selected,
                                               logErrorOnly=bBatchMode,
                                               dryRun=dryRun,
                                               checkSyncState=checkSyncState,)
    numFailure = logData["failed"]
    numLoaded = logData["loaded"]

    numRefs = len(oAstFileRefList)
    w = len(max((r for r, _ in logItems), key=len)) if logItems else 0
    fmt = lambda rn, m: "{0:<{2}}: {1}".format(rn, m, w)

    sSep = "\n- "
    if numFailure:
        sMsgHeader = (" Failed to load {}/{} asset refs as '{}'. "
                      .format(numFailure, numRefs, sRcName))
        displayFunc = pm.displayError
    else:
        sMsgHeader = (" {}/{} asset refs loaded as '{}'. "
                      .format(numLoaded, numRefs, sRcName))
        displayFunc = pm.displayInfo

    sMsgBody = sSep.join(fmt(r, m) for r, m in logItems)
    sMsgEnd = "".center(100, "-")

    sMsg = '\n' + sMsgHeader.center(100, "-") + sSep + sMsgBody + '\n' + sMsgEnd
    if fail and numFailure:
        raise RuntimeError(sMsg)

    if not bBatchMode:
        print sMsg
        displayFunc(sMsgHeader + "More details in Script Editor ----" + (70 * ">"))

def importAssetRefsFromNamespaces(proj, sNmspcList, sRcName):

    sScnNmspcList = mc.namespaceInfo(listOnlyNamespaces=True)

    renderRefDct = {}
    for sNmspc in sNmspcList:

        if sNmspc in sScnNmspcList:
            renderRefDct[sNmspc] = "Namespace already exists."
            continue

        sAstName = "_".join(sNmspc.split("_")[:3])
        try:
            damAst = proj.getAsset(sAstName)
            mrcFile = damAst.getRcFile("public", sRcName, dbNode=False, fail=True)
        except Exception as e:
            renderRefDct[sNmspc] = e
            continue

        renderRefDct[sNmspc] = mrcFile

    for sNmspc, mrcFile in sorted(renderRefDct.iteritems()):
        if not isinstance(mrcFile, DrcEntry):
            continue
        mrcFile.mayaImportScene(ns=sNmspc)

    errorItems = tuple((k, v) for k, v in renderRefDct.iteritems()
                       if isinstance(v, (basestring, Exception)))
    if errorItems:
        print " Import summary ".center(120, "#")
        numErrors = 0
        for sNmspc, e in errorItems:
            sMsg = "'{}': {}".format(sNmspc, toStr(e))
            if isinstance(e, StandardError):
                pm.displayError(sMsg)
                numErrors += 1
            elif isinstance(e, Warning):
                pm.displayWarning(sMsg)
            else:
                pm.displayInfo(sMsg)

        if numErrors:
            pm.displayWarning(" Failed to import {}/{} '{}' "
                              .format(numErrors, len(sNmspcList), sRcName)
                              .center(120, "#"))
        else:
            print 120 * "-"

    return renderRefDct

def listPrevizRefMeshes(project=None):

    proj = project
    if not proj:
        proj = projectFromScene()

    astLib = proj.getLibrary("public", "asset_lib")

    sAllMeshList = []

    oFileRefList = pm.listReferences(unloaded=False, loaded=True)
    for oFileRef in oFileRefList:

        sRefPath = pathResolve(oFileRef.path)

        ctxData = None
        try:
            ctxData = proj.contextFromPath(sRefPath, library=astLib)
        except Exception as e:
            pm.displayWarning(toStr(e))

        if not ctxData:
            continue

        sCurRcName = ctxData.get("resource", "")
        if not sCurRcName.startswith("previz"):
            continue

        sMeshList = mc.referenceQuery(oFileRef.refNode.name(), nodes=True)
        if sMeshList:
            sMeshList = mc.ls(sMeshList, type="mesh", ni=True)
            if sMeshList:
                sAllMeshList.extend(sMeshList)

    return sAllMeshList

def lockAssetRefsToRelatedVersion(relatedAssetList, dryRun=False):

    for relAstData in relatedAssetList:

#        sAstName = relAstData["name"]
#        if not sAstName:
#            continue
#
#        sRcName = relAstData["resource"]
#        if sRcName == noneValue:
#            continue
#
#        rcFile = relAstData.get("rc_entry")
#        if not rcFile:
#            continue

#        if rcFile.isVersionFile():
#            print "'{}' - already locked to '{}'".format(sAstName, rcFile.name)
#            continue

        damAst = relAstData.get("dam_entity")
        if not damAst:
            continue
        sAstName = damAst.name

        versFile = relAstData["version_file"]
        if not versFile:
            print "'{}' - No version file to switch to.".format(sAstName)
            continue

        sRefPath = versFile.envPath()
        for oFileRef in relAstData["file_refs"]:

            cmdFlags = dict()
            if not oFileRef.isLoaded():
                cmdFlags = dict(lrd="none")

            if not dryRun:
                oFileRef.replaceWith(sRefPath, **cmdFlags)

def switchAssetRefsToHeadFile(relatedAssetList, dryRun=False):

    for relAstData in relatedAssetList:

        damAst = relAstData.get("dam_entity")
        if not damAst:
            continue
        #sAstName = damAst.name

        rcFile = relAstData.get("rc_entry")
        if not rcFile:
            continue

        if not rcFile.isVersionFile():
            continue

        try:
            headFile = rcFile.getHeadFile(fail=True, dbNode=False)
        except Exception as e:
            pm.displayWarning(e.message)

        sRefPath = headFile.envPath()
        for oFileRef in relAstData["file_refs"]:

            cmdFlags = dict()
            if not oFileRef.isLoaded():
                cmdFlags = dict(lrd="none")

            if not dryRun:
                oFileRef.replaceWith(sRefPath, **cmdFlags)

def conformAssetRefsToEnvPath(relatedAssetList, dryRun=False):

    for relAstData in relatedAssetList:

        damAst = relAstData.get("dam_entity")
        if not damAst:
            continue
        #sAstName = damAst.name

        rcFile = relAstData.get("rc_entry")
        if not rcFile:
            continue

        sEnvPath = rcFile.envPath()
        for oFileRef in relAstData["file_refs"]:

            if normCase(oFileRef.unresolvedPath()) == normCase(sEnvPath):
                continue

            cmdFlags = dict()
            if not oFileRef.isLoaded():
                cmdFlags = dict(lrd="none")

            if not dryRun:
                oFileRef.replaceWith(sEnvPath, **cmdFlags)

def selectRefsWithDefaultAssetFile(assetFile="NoInput"):

    oRefNodeDct = {}
    for oFileRef in listReferences(loaded=True):
        oRefNode = oFileRef.refNode

        if not oRefNode.hasAttr(DEFAULT_FILE_ATTR):
            continue

        sValue = oRefNode.getAttr(DEFAULT_FILE_ATTR)
        if not sValue:
            continue

        oRefNodeDct.setdefault(sValue, []).append(oRefNode)

    sFoundValues = sorted(oRefNodeDct.iterkeys())

    if not sFoundValues:
        pm.displayWarning("No asset references to select !")

    if assetFile != "NoInput":
        if assetFile not in sFoundValues:
            pm.displayWarning("No refs with default asset file set to '{}'. Found {}."
                              .format(assetFile, sFoundValues))
            return
        sAstRcName = assetFile
    else:
        sChoice = pm.confirmDialog(title="Hey, mon ami !",
                                   message="",
                                   button=sFoundValues + ["Cancel"],
                                   defaultButton='Cancel',
                                   cancelButton='Cancel',
                                   dismissString='Cancel',
                                   icon="question")

        if sChoice == "Cancel":
            pm.displayWarning("Canceled !")
            return
        else:
            sAstRcName = sChoice

    sSelList = []
    count = 0
    for oRefNode in oRefNodeDct[sAstRcName]:

        sRefNode = oRefNode.name()
        sNodeList = mc.referenceQuery(sRefNode, nodes=True, dagPath=True)
        if sNodeList:
            sDagNodeList = mc.ls(sNodeList, type="dagNode")
            if sDagNodeList:
                sNodeList = sDagNodeList
            sNodeList = [sNodeList[0], sRefNode]
        else:
            sNodeList = [sRefNode]

        sSelList.extend(sNodeList)
        count += 1

    if sSelList:
        mc.select(sSelList, replace=True, noExpand=True)
        pm.displayInfo("{} references selected.".format(count))
    else:
        pm.displayWarning("No references to select !")

    return sSelList

class SelectRefDialog(MayaQWidgetDockableMixin, QtGui.QDialog):

    def __init__(self, *args, **kwargs):
        super(SelectRefDialog, self).__init__(*args, **kwargs)

        self.setObjectName("SelectRefDialog")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowTitle("Select Refs With Default Asset File")

        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)

        buttonBox = QtGui.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Horizontal)
        buttonBox.setObjectName("buttonBox")

        btn = buttonBox.addButton("Close", QtGui.QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.accept)
        btn = buttonBox.addButton("Refresh", QtGui.QDialogButtonBox.ResetRole)
        btn.clicked.connect(self.refresh)

        layout.addWidget(buttonBox)

        self.refNodes = {}

        self.selectionButtons = self.createButtons()

    def createButtons(self):

        oRefNodeDct = {}
        for oFileRef in listReferences(loaded=True):
            oRefNode = oFileRef.refNode

            if not oRefNode.hasAttr(DEFAULT_FILE_ATTR):
                continue

            sValue = oRefNode.getAttr(DEFAULT_FILE_ATTR)
            if not sValue:
                continue

            oRefNodeDct.setdefault(sValue, []).append(oRefNode)

        sFoundValues = sorted(oRefNodeDct.iterkeys())

        buttonList = []
        layout = self.layout()

        if not sFoundValues:
#            btn = QtGui.QPushButton("No ref with default asset file.", self)
#            layout.insertWidget(0, btn)
#            buttonList.append(btn)
            return buttonList

        self.refNodes = oRefNodeDct

        for sValue in sFoundValues:
            btn = QtGui.QPushButton(sValue, self)
            buttonList.append(btn)

            layout.insertWidget(0, btn)
            slot = partial(self.selectReferences, sValue)
            btn.clicked.connect(slot)

        return buttonList

    def selectReferences(self, sAstRcName):

        oRefNodeDct = self.refNodes

        sSelList = []
        count = 0
        for oRefNode in oRefNodeDct[sAstRcName]:

            sRefNode = oRefNode.name()
            sNodeList = mc.referenceQuery(sRefNode, nodes=True, dagPath=True)
            if sNodeList:
                sDagNodeList = mc.ls(sNodeList, type="dagNode")
                if sDagNodeList:
                    sNodeList = sDagNodeList
                sNodeList = [sNodeList[0], sRefNode]
            else:
                sNodeList = [sRefNode]

            sSelList.extend(sNodeList)
            count += 1

        if sSelList:
            mc.select(sSelList, replace=True, noExpand=True)
            pm.displayInfo("{} references selected.".format(count))
        else:
            pm.displayWarning("No references to select !")

    def refresh(self):

        layout = self.layout()
        for btn in self.selectionButtons:
            btn.close()
            layout.removeWidget(btn)
            btn.deleteLater()

        self.selectionButtons = self.createButtons()




