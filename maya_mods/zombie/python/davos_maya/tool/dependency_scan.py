
import os
import os.path as osp
import re

from PySide import QtGui
from PySide.QtCore import Qt, QSize

import PIL.Image
import filecmp
pilimage = PIL.Image

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import pymel.core as pm

from pytd.gui.dialogs import QuickTreeDialog, confirmDialog
from pytd.gui.widgets import QuickTree, QuickTreeItem
#from pytd.util.logutils import logMsg
from pytaya.core.general import lsNodes

from pytd.util.fsutils import pathResolve, normCase, pathJoin
from pytd.util.fsutils import ignorePatterns, iterPaths
from pytd.util.strutils import labelify, assertChars
from pytd.util.qtutils import setWaitCursor
from pytd.util.sysutils import argToTuple, toStr, inDevMode

from .general import entityFromScene

mainWin = None

FILE_ITEM_TYPE = 1000
NODE_ITEM_TYPE = FILE_ITEM_TYPE + 1

class WrappedNode(object):

    def __init__(self, node):
        self.node = node

    def __repr__(self):
        return "Wrapped" + self.node.__repr__().split(".", 1)[-1]

class DependencyTreeItem(QuickTreeItem):

    def __init__(self, parent, texts, **kwargs):
        super(DependencyTreeItem, self).__init__(parent, texts, **kwargs)

        if isinstance(parent, DependencyTreeItem):

            if self.type() != NODE_ITEM_TYPE:

                for c in xrange(self.columnCount()):

                    brush = parent.data(c, Qt.ForegroundRole)
                    if brush:
                        self.setForeground(c, brush)

                    brush = parent.data(c, Qt.BackgroundRole)
                    if brush:
                        self.setBackground(c, brush)

class ItemDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(ItemDelegate, self).__init__(parent)

    def sizeHint(self, option, index):
        return QtGui.QStyledItemDelegate.sizeHint(self, option, index) + QSize(4, 4)

class DependencyTree(QuickTree):

    def __init__(self, parent):
        super(DependencyTree, self).__init__(parent)

        self.defaultFlags |= Qt.ItemIsEditable

        self.itemClass = DependencyTreeItem

        QT_STYLE = QtGui.QStyleFactory.create("Plastique")
        self.setStyle(QT_STYLE)
        self.setAlternatingRowColors(True)
        self.setItemDelegate(ItemDelegate(self))

    def _onItemClicked(self, item):
        userData = item.data(0, Qt.UserRole)
        if userData:
            wrappedNodes = argToTuple(userData)
            pm.select(tuple(wn.node for wn in wrappedNodes))
        else:
            pm.select(cl=True)

class DependencyTreeDialog(MayaQWidgetBaseMixin, QuickTreeDialog):

    def __init__(self, parent=None, scanFunc=None):
        super(DependencyTreeDialog, self).__init__(parent=parent)

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setTreeWidget(DependencyTree(self))
        self.resize(900, 600)

        self.scanResults = None
        self.__scanFunc = scanFunc if scanFunc else scanTextureDependency

        self.refreshBtn = self.buttonBox.addButton("Refresh", QtGui.QDialogButtonBox.ResetRole)
        self.refreshBtn.clicked.connect(self.refresh)

    def refresh(self):
        self.treeWidget.clear()
        self.setupTreeData(self.__scanFunc(entityFromScene()))

    def setupTreeData(self, scanResults, allExpanded=False):

        self.scanResults = scanResults
        if not scanResults:
            return

        treeWidget = self.treeWidget

        sHeaderList = ["Files", "Summary", "Description"]
        treeWidget.setHeaderLabels(sHeaderList)

        sAllSeveritySet = scanResults[-1]["scan_severities"]

        sFileGrpItems = set()
        treeData = []
        for result in scanResults:

            fileNodes = result["file_nodes"]
            sFileNodeNames = tuple(n.name()for n in fileNodes)

            wrappedNodes = []
            numNodes = 0
            sNumNodes = ""

            if fileNodes:
                fileNodeTreeData = {}
                for fileNode in fileNodes:

                    sNodeName = fileNode.name()

                    wrappedNode = WrappedNode(fileNode)
                    wrappedNodes.append(wrappedNode)

                    itemData = {"texts": [sNodeName, "", fileNode.getAttr("fileTextureName")],
                                "roles":{Qt.UserRole:(0, wrappedNode)},
                                "type":NODE_ITEM_TYPE
                                }
                    fileNodeTreeData[sNodeName] = itemData

                numNodes = len(fileNodes)
                sNumNodes = "{} {}".format(numNodes, "nodes" if numNodes > 1 else "node")

            sTexAbsPath = result["abs_path"]
            sFilename = osp.basename(sTexAbsPath)

            scanLogDct = result["scan_log"]

            for sSeverity, logItemsList in scanLogDct.iteritems():

                sSeverityTitle = (sSeverity + 's').upper()

                for sLogCode, sLogMsg in logItemsList:

                    sItemPath = pathJoin(sSeverityTitle, labelify(sLogCode))
                    sFileGrpItems.add(sItemPath)
                    sItemPath = pathJoin(sItemPath, sFilename)

                    itemRoles = {Qt.UserRole:(0, wrappedNodes)}

                    itemData = {"path": sItemPath,
                                "texts": [sFilename, sNumNodes, sLogMsg.strip().rstrip('.')],
                                "roles":itemRoles,
                                "type":FILE_ITEM_TYPE
                                }
                    treeData.append(itemData)

                    for sNodeName in sFileNodeNames:
                        itemData = fileNodeTreeData[sNodeName].copy()
                        itemData["path"] = pathJoin(sItemPath, sNodeName)
                        treeData.append(itemData)

        numCol = treeWidget.columnCount()
        serverityItems = (("info", Qt.green), ("warning", Qt.yellow), ("error", Qt.red))
        for sSeverity, qtcolor in serverityItems:

            if sSeverity not in sAllSeveritySet:
                continue

            color = QtGui.QColor(qtcolor)
            color.setAlpha(35)

            itemData = {"path": (sSeverity + 's').upper(),
                        #"texts": [sFilename, sNumNodes, sMsg],
                        "roles":{#Qt.ForegroundRole:(0, QtGui.QBrush(qtcolor)),
                                 Qt.BackgroundRole:(xrange(numCol), QtGui.QBrush(color)), },
                        }
            treeData.insert(0, itemData)

        if scanResults[-1]["publish_count"]:
            p = pathJoin(("info" + 's').upper(), labelify("ReadyToPublish"))
            itemData = {"path": p,
                        #"texts": [sFilename, sNumNodes, sMsg],
                        "roles":{#Qt.ForegroundRole:(0, QtGui.QBrush(qtcolor)),
                                 Qt.ForegroundRole:(0, QtGui.QBrush(Qt.green)), },
                        }
            treeData.append(itemData)

        treeWidget.createTree(treeData)

        if len(sFileGrpItems) == 1:
            allExpanded = True

        c = sHeaderList.index("Summary")
        for sItemPath in sFileGrpItems:
            item = treeWidget.itemFromPath(sItemPath)
            item.setText(c, "{} files".format(item.childCount()))
            if allExpanded:
                item.setExpanded(True)

        for i in xrange(treeWidget.topLevelItemCount()):
            item = treeWidget.topLevelItem(i)
            item.setExpanded(True)

UDIM_MODE = 3
UDIM_RGX = r"\.1\d{3}\."

def makeUdimFilePattern(p):
    return re.sub(UDIM_RGX, ".1*.", osp.basename(p))

@setWaitCursor
def scanTextureDependency(damEntity):

    proj = damEntity.project
    sAstName = damEntity.name
    try:
        sPrivTexDirPath = damEntity.getPath("private", "texture_dir")
    except AttributeError as e:
        pm.displayInfo(toStr(e))
        return []

    sPubTexDirPath = damEntity.getPath("public", "texture_dir")
    if osp.exists(sPubTexDirPath):
        pubTexDir = proj.entryFromPath(sPubTexDirPath)
        pubTexDir.loadChildDbNodes()

    sAllowedTexTypes = proj.getVar("project", "allowed_texture_formats")

    allFileNodes = lsNodes("*", type='file', not_rn=True)
    scanResults = []
    fileNodeDct = {}

    sAllSeveritySet = set()
    sFoundFileList = []
    sPrivFileList = []
    publishCount = 0

    def addResult(res):
#        for k, v in res.iteritems(): print k, v
#        print ""
        scanResults.append(res)
        sAllSeveritySet.update(res["scan_log"].iterkeys())


    for fileNode in allFileNodes:

        sNodePath = fileNode.getAttr("fileTextureName")
        if not sNodePath:
            continue

        sNodeAbsPath = pathResolve(sNodePath)
        sNodeNormPath = normCase(sNodeAbsPath)

        iTilingMode = fileNode.getAttr("uvTilingMode")
        bUvTileOn = (iTilingMode != 0)
        bUdimMode = (iTilingMode == UDIM_MODE)

        sUdimPathList = []
        sTexAbsPathList = (sNodeAbsPath,)
        if bUdimMode and osp.isfile(sNodeAbsPath):
            sUdimPat = makeUdimFilePattern(sNodeAbsPath)
            sTexAbsPathList = sorted(iterPaths(osp.dirname(sNodeAbsPath), dirs=False,
                                               recursive=False,
                                               keepFiles=ignorePatterns(sUdimPat)
                                               ))
            sUdimPathList = sTexAbsPathList[:]

        for sTexAbsPath in sTexAbsPathList:

            scanLogDct = {}
            resultDct = {}
            foundBudResList = []

            sTexNormPath = normCase(sTexAbsPath)
            bNodePath = (sTexNormPath == sNodeNormPath)
            if sTexNormPath in fileNodeDct:
                if bNodePath:
                    fileNodeDct[sTexNormPath].append(fileNode)
                continue
            else:
                fileNodeDct[sTexNormPath] = [fileNode] if bNodePath else []

            if bUvTileOn and (not bUdimMode):
                sMsg = "Only UDIM (Mari) accepted"
                scanLogDct.setdefault("error", []).append(('BadUVTilingMode', sMsg))

            sTexDirPath, sTexFilename = osp.split(sTexAbsPath)
            sBasePath, sExt = osp.splitext(sTexAbsPath)

            bPublicFile = False
            sHighSeverity = "error"
            texFile = None
            bExists = osp.isfile(sTexAbsPath)

            resultDct = {"abs_path":sTexAbsPath,
                         "scan_log":scanLogDct,
                         "file_nodes":fileNodeDct[sTexNormPath],
                         "buddy_paths":[],
                         "udim_paths":sUdimPathList,
                         "publishable":False,
                         "drc_file":None,
                         "exists":bExists,
                         }

            if not bExists:
                scanLogDct.setdefault("error", []).append(('FileNotFound', sTexAbsPath))
                addResult(resultDct)
                continue
            else:
                sFoundFileList.append(sTexNormPath)
                texFile = proj.entryFromPath(sTexAbsPath)

                resultDct["drc_file"] = texFile

                if texFile and texFile.isPublic():

                    bPublicFile = True
                    sHighSeverity = "warning"

                    scanLogDct.setdefault("info", []).append(('PublicFiles', sTexAbsPath))

                    if normCase(sTexDirPath) == normCase(sPubTexDirPath):
                        privFile = texFile.getPrivateFile(weak=True)
                        sPrivFileList.append(normCase(privFile.absPath()))

            sTiling = ""
            if len(re.findall(UDIM_RGX, sTexFilename)) != 1:
                if bUdimMode:
                    sMsg = "Must match 'name.1###.ext' pattern"
                    scanLogDct.setdefault(sHighSeverity, []).append(('BadUDIMFilename', sMsg))
            else:
                sBasePath, sTiling = sBasePath.rsplit('.', 1)
                if not bUdimMode:
                    sMsg = "UDIM mode is OFF"
                    scanLogDct.setdefault(sHighSeverity, []).append(('BadUVTilingMode', sMsg))

            sBaseName = osp.basename(sBasePath)

            if sExt.lower() not in sAllowedTexTypes:
                sMsg = ("Only accepts: '{}'".format("' '".join(sAllowedTexTypes)))
                scanLogDct.setdefault(sHighSeverity, []).append(('BadTextureFormat', sMsg))

            if (not bPublicFile) and (normCase(sTexDirPath) != normCase(sPrivTexDirPath)):
                sMsg = ("Not in '{}'".format(osp.normpath(sPrivTexDirPath)))
                scanLogDct.setdefault(sHighSeverity, []).append(('BadLocation', sMsg))

            sMsg = ""
            sChannel = ""
            if sTexFilename.lower().startswith(sAstName.lower()):
                sMsg = ("Must NOT start with the asset name")
            else:
                try:
                    assertChars(sBaseName, r"[\w]")
                except AssertionError, e:
                    sMsg = toStr(e)
                else:
                    sNameParts = sBaseName.split("_")
                    if len(sNameParts) not in (3, 4):
                        sMsg = "Must have 3 or 4 parts: tex_textureSubject_[optional]_channel"
                    elif sNameParts[0] != "tex":
                        sMsg = ("Must start with 'tex_'")
                    else:
                        sChannel = sNameParts[-1]
                        if len(sChannel) != 3:
                            sMsg = ("Channel can only have 3 characters, got {} in '{}'"
                                    .format(len(sChannel), sChannel))

            if sMsg and (not bPublicFile):
                scanLogDct.setdefault(sHighSeverity, []).append(('BadFilename', sMsg))
                sMsg = ""

            if sExt == ".tga":

                bColor = (sChannel == "col")
                sPsdSeverity = sHighSeverity if bColor else "info"
                sBuddyItems = [(".tx", "warning"), (".psd", sPsdSeverity)]

                if bColor:
                    sBuddyItems.append(("HD.jpg", "info"))

                for sBuddySfx, sBudSeverity in sBuddyItems:

                    sSuffix = sBuddySfx
                    if sTiling and ("." in sBuddySfx):
                        sSuffix = sBuddySfx.replace(".", "." + sTiling + ".")
                    sBuddyPath = "".join((sBasePath, sSuffix))

                    if not osp.isfile(sBuddyPath):
                        if not bPublicFile:
                            sBuddyLabel = "".join(s.capitalize()for s in sBuddySfx.split("."))
                            sStatusCode = sBuddyLabel.upper() + "FileNotFound"
                            if sBudSeverity != "info":
                                scanLogDct.setdefault(sBudSeverity, []).append((sStatusCode, sBuddyPath))
                    else:
                        sFoundFileList.append(normCase(sBuddyPath))

                        budScanLogDct = {}
                        budFile = proj.entryFromPath(sBuddyPath)
                        if budFile and budFile.isPublic():

                            budScanLogDct.setdefault("info", []).append(('PublicFiles', sBuddyPath))

                            if normCase(osp.dirname(sBuddyPath)) == normCase(sPubTexDirPath):
                                privBudFile = budFile.getPrivateFile(weak=True)
                                sPrivFileList.append(normCase(privBudFile.absPath()))

                        budResultDct = {"abs_path":sBuddyPath,
                                        "scan_log":budScanLogDct,
                                        "file_nodes":[],
                                        "buddy_paths":[],
                                        "udim_paths":[],
                                        "publishable":False,
                                        "drc_file":budFile,
                                        "exists":True,
                                        }
                        foundBudResList.append(budResultDct)

                if (not bPublicFile):
                    tgaImg = None
                    try:
                        tgaImg = pilimage.open(sTexAbsPath)
                        tileInfo = tgaImg.tile[0]
                        sCompress = tileInfo[0]
                        sMode = tileInfo[-1][0]

                        bRgb24 = (sMode == "BGR")
                        bCompr = (sCompress == "tga_rle")

                        sMsgList = []
                        if not bCompr:
                            sMsgList.append("NOT COMPRESSED")

                        if not bRgb24:
                            depthDct = {"BGR;5": 16, "BGR":24, "BGRA":32,
                                        "RGB;5": 16, "RGB":24, "RGBA":32}
                            sMsg = "Expected 24 bits, got {} bits".format(depthDct[sMode])
                            sMsgList.append(sMsg)

                        if sMsgList:
                            sMsg = "\n".join(sMsgList)
                            scanLogDct.setdefault(sHighSeverity, []).append(("BadTargaFormat", sMsg))
                    finally:
                        if tgaImg:
                            tgaImg.close()
                        else:
                            sMsg = "Could not read the file"
                            scanLogDct.setdefault(sHighSeverity, []).append(("BadTargaFormat", sMsg))

            resultDctList = [resultDct]
            if foundBudResList:
                resultDctList.extend(foundBudResList)
                sBuddyFileList = list(brd["abs_path"] for brd in foundBudResList)
                resultDct["buddy_paths"] = sBuddyFileList

            for resDct in resultDctList:
                if resDct["exists"]:
                    _setPublishableState(resDct)
                    if resDct["publishable"]:
                        publishCount += 1
                addResult(resDct)

    sAllowedFileTypes = [".tx", ".psd"]
    sAllowedFileTypes.extend(sAllowedTexTypes)
    #looking for unused files in texture direcotry
    if osp.isdir(sPrivTexDirPath):

        sTexDirFileList = sorted(iterPaths(sPrivTexDirPath, dirs=False, recursive=False))

        for p in sTexDirFileList:

            scanLogDct = {}

            sExt = osp.splitext(p)[-1]
            if sExt.lower() not in sAllowedFileTypes:
                continue

            np = normCase(p)

            if np in sPrivFileList:
                pass#scanLogDct.setdefault("info", []).append(("AlreadyPublished", p))
            elif np not in sFoundFileList:
                scanLogDct.setdefault("warning", []).append(("UnusedPrivateFiles", p))
            else:
                continue

            resultDct = {"abs_path":p,
                         "scan_log":scanLogDct,
                         "file_nodes":[],
                         "buddy_paths":[],
                         "udim_paths":[],
                         "publishable":False,
                         "drc_file":None,
                         }
            addResult(resultDct)

    if scanResults:
        scanResults[-1]["scan_severities"] = sAllSeveritySet
        scanResults[-1]["publish_count"] = publishCount

    return scanResults

def _setPublishableState(resultDct):

    scanLogDct = resultDct["scan_log"]
    if "error" in scanLogDct:
        return

    drcFile = resultDct["drc_file"]
    if not drcFile:
        return

    if not drcFile.isPrivate():
        return

    bPublishable = False

    bUpToDate = True
    pubFile = drcFile.getPublicFile(weak=True)
    if pubFile.exists():
        bUpToDate = pubFile.isUpToDate()

#    bOldPrivFile = False
#    privFsMtime = drcFile.fsMtime
#    pubDbMtime = pubFile.dbMtime
#    if (pubFile.currentVersion > 0) and (privFsMtime < pubDbMtime):
#        bOldPrivFile = True
#        sFmt = "%Y-%m-%d %H:%M"
#        sCurTime = privFsMtime.strftime(sFmt)
#        sPubTime = pubDbMtime.strftime(sFmt)
#
#    if bOldPrivFile:
#        sMsg = ("File is OBSOLETE: \n yours: {}\npublic: {}"
#                .format(sCurTime, sPubTime))
#        scanLogDct.setdefault("error", []).append(("NotPublishable", sMsg))

    if not bUpToDate:
        sMsg = """Public file appears to have been modified from another site.
Wait for the next file synchronization and retry publishing."""
        scanLogDct.setdefault("error", []).append(("NotPublishable", sMsg))
    else:
        sSrcFilePath = resultDct["abs_path"]
        bModified = True
        if pubFile.exists():
            sPubFilePath = pubFile.absPath()
            bModified = (not filecmp.cmp(sSrcFilePath, sPubFilePath))
            #bDiffers, sSrcChecksum = pubFile.differsFrom(sPubFilePath)

        if not bModified:
            scanLogDct.setdefault("info", []).append(("Not Modified", "File has not been modified"))
        else:
            bPublishable = True

            sMsg = ""
            sBuddyFileList = resultDct["buddy_paths"]
            if sBuddyFileList:
                sExtList = tuple(osp.splitext(p)[-1] for p in sBuddyFileList)
                sMsg = (", ".join(s.upper() for s in sExtList) + " found"
                        if sBuddyFileList else "")
            elif inDevMode():
                sMsg = resultDct["abs_path"]

            scanLogDct.setdefault("info", []).append(("ReadyToPublish", sMsg))

    resultDct["publishable"] = bPublishable

dialog = None

def launch(damEntity=None, scanFunc=None, modal=False, okLabel="OK",
           expandTree=False, forceDialog=False):

    global dialog

    if not damEntity:
        damEntity = entityFromScene()

    if scanFunc is None:
        scanResults = scanTextureDependency(damEntity)
    else:
        scanResults = scanFunc(damEntity)

    if not scanResults:
        return scanResults

    if not forceDialog:
        sScanSeverities = scanResults[-1]["scan_severities"]
        if not sScanSeverities:
            return scanResults

    dialog = DependencyTreeDialog(scanFunc=scanFunc)

    l = ("Dependencies Status", damEntity.name, damEntity.project.name.capitalize())
    dialog.setWindowTitle(" - ".join(l))

    buttonBox = dialog.buttonBox
    okBtn = buttonBox.button(QtGui.QDialogButtonBox.Ok)

    err = None
    if "error" in scanResults[-1]["scan_severities"]:

        err = RuntimeError("Please, fix the following errors and retry...")

        buttonBox.removeButton(okBtn)
        btn = buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        btn.setText("Close")
    else:
        if modal:
            okBtn.setText(okLabel)

    dialog.show()
    dialog.setupTreeData(scanResults, allExpanded=expandTree)

    if modal:
        if err:
            confirmDialog(title='SORRY !',
                          message=toStr(err),
                          button=["OK"],
                          defaultButton="OK",
                          cancelButton="OK",
                          dismissString="OK",
                          icon="critical",
                          parent=dialog
                          )
            raise err

        dialog.close()
        if dialog.exec_():
            return dialog.scanResults

    return None

