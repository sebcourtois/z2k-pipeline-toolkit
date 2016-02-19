
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

from davos_maya.tool.general import entityFromScene


@processSelectedReferences
def listMayaRcForSelectedRefs(oFileRef, project, **kwargs):

    sRefPath = pathResolve(oFileRef.path)
    asset = project.entityFromPath(sRefPath, fail=False)

    mayaRcDct = dict()
    if asset:
        mayaRcDct = dict((rc, p if normCase(p) != normCase(sRefPath) else "current")
                                    for rc, p in asset.iterMayaRcItems(**kwargs))
    res = (asset, mayaRcDct)

    resultList = kwargs.pop("processResults")
    resultList.append(res)

@withSelectionRestored
def switchSelectedReferences(dryRun=False, **kwargs):

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
    nonSwitchedRefList = []
    for oFileRef, assetRc in izip(oSelRefList, assetRcList):

        asset = assetRc[0]
        rcDct = assetRc[1]

        i += 1
        print "Switching {}/{}: '{}' ...".format(i, numRefs, oFileRef.refNode.name())

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
            sMsg = "{} has no such resource: '{}'".format(asset, sChosenRcName)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if sRcPath == "current":
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

        cachedDbNode = mrcFile.getDbNode(fromDb=False)
        if cachedDbNode:
            mrcFile.refresh(simple=True)
        else:
            mrcFile.getDbNode(fromCache=False)

        if not mrcFile.currentVersion:
            sMsg = "No version created yet: '{}'".format(sRcPath)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if not mrcFile.isUpToDate(refresh=False):
            sMsg = "File is out of sync: '{}'".format(sRcPath)
            nonSwitchedRefList.append((oFileRef, sMsg))
            print sMsg
            continue

        if not dryRun:
            try:
                oFileRef.replaceWith(mrcFile.envPath())
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

    kwargs.update(confirm=False, allIfNoSelection=False, topReference=True)
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

def loadReferencesForAnim(dryRun=False):

    scnEntity = entityFromScene()
    proj = scnEntity.project

    logItems = []
    numFailure = 0
    numLoaded = 0
    oFileRefList = pm.listReferences(unloaded=True, loaded=False)
    for oFileRef in oFileRefList:

        sDefaultRcName = ""
        oRefNode = oFileRef.refNode
        sRefNode = oRefNode.name()
        if oRefNode.hasAttr(DEFAULT_FILE_ATTR):
            sDefaultRcName = oRefNode.getAttr(DEFAULT_FILE_ATTR)

        if sDefaultRcName == "offloaded":
            logItems.append((sRefNode, "kept offloaded"))
            continue

        sRefPath = pathResolve(oFileRef.path)

        pathData = None
        try:
            pathData = proj.dataFromPath(sRefPath)
        except Exception as e:
            pm.displayWarning(toStr(e))

        sCurRcName = pathData.get("resource", "")
        if sDefaultRcName in set(("", sCurRcName)):
            sMsg = "loaded as '{}'".format(sDefaultRcName) if sDefaultRcName else "loaded"
            logItems.append((sRefNode, sMsg))
            if not dryRun:
                oFileRef.load()
            numLoaded += 1
            continue

        try:
            asset = proj._entityFromPathData(pathData, fail=True)
        except Exception as e:
            logItems.append((sRefNode, "FAILED: " + toStr(e)))
            numFailure += 1
            continue

        try:
            astFile = asset.getResource("public", sDefaultRcName,
                                        dbNode=False, fail=True)
        except Exception as e:
            logItems.append((sRefNode, "FAILED: " + toStr(e)))
            numFailure += 1
            continue

        logItems.append((sRefNode, "loaded as '{}'".format(sDefaultRcName)))
        if not dryRun:
            oFileRef.load(astFile.envPath())
        numLoaded += 1

    numRefs = len(oFileRefList)
    w = len(max((r for r, _ in logItems), key=len))
    fmt = lambda rn, m: "{0:<{2}}: {1}".format(rn, m, w)

    sSep = "\n- "
    if numFailure:
        sMsgHeader = " Failed to load {}/{} references. ".format(numFailure, numRefs)
        displayFunc = pm.displayError
    else:
        sMsgHeader = " {}/{} references loaded. ".format(numLoaded, numRefs)
        displayFunc = pm.displayInfo

    sMsgBody = sSep.join(fmt(r, m) for r, m in logItems)
    sMsgEnd = "".center(100, "-")

    sMsg = '\n' + sMsgHeader.center(100, "-") + sSep + sMsgBody + '\n' + sMsgEnd
    print sMsg
    displayFunc(sMsgHeader + "More details in Script Editor ----" + (70 * ">"))

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




