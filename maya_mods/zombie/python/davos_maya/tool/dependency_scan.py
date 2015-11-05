
import os.path as osp
import re

from PySide import QtGui
from PySide.QtCore import Qt, QSize

import PIL.Image
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
from pytd.util.sysutils import argToTuple, toStr

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

    def __init__(self, parent=None):
        super(DependencyTreeDialog, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setTreeWidget(DependencyTree(self))
        self.resize(900, 600)

        self.refreshBtn = self.buttonBox.addButton("Refresh", QtGui.QDialogButtonBox.ResetRole)
        self.refreshBtn.clicked.connect(self.refresh)

    def refresh(self):
        self.treeWidget.clear()
        self.setupTreeData(scanTextureDependency(entityFromScene()))

    def setupTreeData(self, scanResults):

        treeWidget = self.treeWidget

        sHeaderList = ["Files", "Summary", "Description"]
        treeWidget.setHeaderLabels(sHeaderList)

        sAllSeveritySet = scanResults[-1]["scan_severities"]
        print "-------------", sAllSeveritySet

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

                    if (sLogCode == "ReadyToPublish"):
                        sBuddyFileList = result["buddy_files"]
                        for sBuddyPath in sBuddyFileList:

                            sBudFilename = osp.basename(sBuddyPath)
                            itemData = {"path": pathJoin(sItemPath, sBudFilename),
                                        "texts": [sBudFilename, "", sBuddyPath],
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

        c = sHeaderList.index("Summary")
        for sItemPath in sFileGrpItems:
            item = treeWidget.itemFromPath(sItemPath)
            item.setText(c, "{} files".format(item.childCount()))

        for i in xrange(treeWidget.topLevelItemCount()):
            item = treeWidget.topLevelItem(i)
            item.setExpanded(True)

UDIM_MODE = 3
UDIM_RGX = r"\.1\d{3}\."

@setWaitCursor
def scanTextureDependency(damAst):

    proj = damAst.project
    sAstName = damAst.name
    sPrivTexDirPath = damAst.getPath("private", "texture_dir")
    sPubTexDirPath = damAst.getPath("public", "texture_dir")
    sAllowTexTypes = proj.getVar("project", "allowed_texture_formats")

    allFileNodes = lsNodes("*", type='file', not_rn=True)
    scanResults = []
    fileNodeDct = {}

    sAllSeveritySet = set()
    sFoundFileList = []
    publishCount = 0

    def addResult(res):
#        for k, v in res.iteritems(): print k, v
#        print ""
        scanResults.append(res)
        sAllSeveritySet.update(res["scan_log"].iterkeys())

    for fileNode in allFileNodes:

        sTexPath = fileNode.getAttr("fileTextureName")
        if not sTexPath:
            continue

        iTilingMode = fileNode.getAttr("uvTilingMode")
        bUvTileOn = (iTilingMode != 0)
        bUdim = (iTilingMode == UDIM_MODE)

        sTexAbsPath = pathResolve(sTexPath)
        drcFile = proj.entryFromPath(sTexAbsPath, dbNode=False)

        sTexAbsPathList = (sTexAbsPath,)
        if bUdim and drcFile:
            sFilename = re.sub(UDIM_RGX, ".1*.", osp.basename(sTexAbsPath))
            sDirPath = drcFile.parentDir().absPath()
            sTexAbsPathList = sorted(iterPaths(sDirPath, dirs=False,
                                             recursive=False,
                                             keepFiles=ignorePatterns(sFilename)
                                             )
                                     )

        for sTexAbsPath in sTexAbsPathList:

            scanLogDct = {}
            resultDct = {}
            sBuddyFileList = []

            sNormTexPath = normCase(sTexAbsPath)
            if sNormTexPath in fileNodeDct:
                fileNodeDct[sNormTexPath].append(fileNode)
                continue
            else:
                fileNodeDct[sNormTexPath] = [fileNode]

            if bUvTileOn and (not bUdim):
                sMsg = "Only UDIM (Mari) accepted"
                scanLogDct.setdefault("error", []).append(('BadUvTilingMode', sMsg))

            sDirPath, sFilename = osp.split(sTexAbsPath)
            sBasePath, sExt = osp.splitext(sTexAbsPath)

            drcFile = None
            bExists = osp.isfile(sTexAbsPath) or bUdim
            if not bExists:
                scanLogDct.setdefault("error", []).append(('FileNotFound', sTexAbsPath))
            else:
                sFoundFileList.append(normCase(sTexAbsPath))
                drcFile = proj.entryFromPath(sTexAbsPath)
                #print drcFile, drcFile.absPath()
                if drcFile and drcFile.isPublic():
                    if normCase(sDirPath) == normCase(sPubTexDirPath):

                        scanLogDct.setdefault("info", []).append(('AlreadyPublished', sTexAbsPath))

                        resultDct = {"abs_path":sTexAbsPath,
                                     "scan_log":scanLogDct,
                                     "file_nodes":fileNodeDct[sNormTexPath],
                                     "buddy_files":sBuddyFileList,
                                     "publish_ok":False,
                                     "drc_file":drcFile,
                                     }
                        addResult(resultDct)
                        continue

            sTiling = ""
            if bUdim:
                if len(re.findall(UDIM_RGX, sFilename)) != 1:
                    sMsg = "Must match 'name.1###.ext' pattern"
                    scanLogDct.setdefault("error", []).append(('BadUDIMFilename', sMsg))
                else:
                    sBasePath, sTiling = sBasePath.rsplit('.', 1)

            sBaseName = osp.basename(sBasePath)

            if sExt.lower() not in sAllowTexTypes:
                sMsg = ("Only accepts: '{}'".format("' '".join(sAllowTexTypes)))
                scanLogDct.setdefault("error", []).append(('BadTextureFormat', sMsg))

            if normCase(sDirPath) != normCase(sPrivTexDirPath):
                sMsg = ("Not in '{}'".format(osp.normpath(sPrivTexDirPath)))
                scanLogDct.setdefault("error", []).append(('BadLocation', sMsg))

            sMsg = ""
            sChannel = ""
            if sFilename.lower().startswith(sAstName.lower()):
                sMsg = ("Must NOT start with the asset name")
            else:
                try:
                    assertChars(sBaseName, r"[\w]")
                except AssertionError, e:
                    sMsg = toStr(e)
                else:
                    sNameParts = sBaseName.split("_")
                    if len(sNameParts) != 3:
                        sMsg = "Must have 3 parts: tex_textureSubject_channel"
                    elif sNameParts[0] != "tex":
                        sMsg = ("Must start with 'tex_'")
                    else:
                        sChannel = sNameParts[-1]
                        if len(sChannel) != 3:
                            sMsg = ("Channel can only have 3 characters, got {} in '{}'"
                                    .format(len(sChannel), sChannel))
            if sMsg:
                scanLogDct.setdefault("error", []).append(('BadFilename', sMsg))
                sMsg = ""

            if sExt == ".tga":

                bColor = (sChannel == "col")
                sPsdSeverity = "error" if bColor else "info"
                sBuddyItems = [(".tx", "error"), (".psd", sPsdSeverity)]

                if bColor:
                    sBuddyItems.append(("HD.jpg", "info"))

                for sBuddySfx, sSeveriry in sBuddyItems:

                    sSuffix = sBuddySfx
                    if sTiling and ("."in sBuddySfx):
                        sSuffix = sBuddySfx.replace(".", "." + sTiling + ".")
                    sBuddyPath = "".join((sBasePath, sSuffix))

                    if not osp.isfile(sBuddyPath):
                        sBuddyLabel = "".join(s.capitalize()for s in sBuddySfx.split("."))
                        sErrCode = sBuddyLabel + "FileNotFound"
                        scanLogDct.setdefault(sSeveriry, []).append((sErrCode, sBuddyPath))
                    else:
                        sFoundFileList.append(normCase(sBuddyPath))
                        sBuddyFileList.append(sBuddyPath)

                if bExists:
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
                            depthDct = {"BGR;5": 16, "BGR":24, "BGRA":32}
                            sMsg = "Expected 24 bits, got {} bits".format(depthDct[sMode])
                            sMsgList.append(sMsg)

                        if sMsgList:
                            sMsg = "\n".join(sMsgList)
                            scanLogDct.setdefault("error", []).append(("BadTargaFormat", sMsg))
                    finally:
                        tgaImg.close()

            bPublish = False
            if bExists and drcFile and ("error" not in scanLogDct.keys()):

                if drcFile.isPrivate():

                    bUpToDate = True
                    bOldPrivFile = False

                    pubFile = drcFile.getPublicFile(weak=True)
                    bUpToDate = pubFile.isUpToDate()

                    privFsMtime = drcFile.fsMtime
                    pubDbMtime = pubFile.dbMtime
                    if (pubFile.currentVersion > 0) and (privFsMtime < pubDbMtime):
                        bOldPrivFile = True
                        sFmt = "%Y-%m-%d %H:%M"
                        sCurTime = privFsMtime.strftime(sFmt)
                        sPubTime = pubDbMtime.strftime(sFmt)

                    if bOldPrivFile:
                        sMsg = ("File is OBSOLETE: \n yours: {}\npublic: {}"
                                .format(sCurTime, sPubTime))
                        scanLogDct.setdefault("error", []).append(("NotPublishable", sMsg))
                    elif not bUpToDate:
                        sMsg = "Public file is OUT OF SYNC"
                        scanLogDct.setdefault("error", []).append(("NotPublishable", sMsg))
                    else:
                        publishCount += 1
                        bPublish = True

                        sExtList = tuple(osp.splitext(p)[-1] for p in sBuddyFileList)
                        sMsg = (", ".join(s.upper() for s in sExtList) + " found"
                                if sBuddyFileList else "")

                        scanLogDct.setdefault("info", []).append(("ReadyToPublish", sMsg))

            resultDct = {"abs_path":sTexAbsPath,
                         "scan_log":scanLogDct,
                         "file_nodes":fileNodeDct[sNormTexPath],
                         "buddy_files":sBuddyFileList,
                         "publish_ok":bPublish,
                         "drc_file":drcFile,
                         }
            addResult(resultDct)

    #looking for unused files in texture direcotry
    if osp.isdir(sPrivTexDirPath):
        sTexDirFileList = sorted(iterPaths(sPrivTexDirPath, dirs=False, recursive=False))

        numUnused = 0
        for p in sTexDirFileList:

            if normCase(p) in sFoundFileList:
                continue

            sExt = osp.splitext(p)[-1]
            if sExt.lower() not in sAllowTexTypes:
                continue

            scanLogDct = {"warning":[("UnusedPrivateFiles", p)]}

            resultDct = {"abs_path":p,
                         "scan_log":scanLogDct,
                         "file_nodes":[],
                         "buddy_files":[],
                         "publish_ok":False,
                         "drc_file":None,
                         }
            addResult(resultDct)

            numUnused += 1

        if numUnused:
            sAllSeveritySet.add("warning")

    if scanResults:
        scanResults[-1]["scan_severities"] = sAllSeveritySet
        scanResults[-1]["publish_count"] = publishCount

    return scanResults

dialog = None

def launch(damEntity=None, modal=False):

    global dialog

    if not damEntity:
        damEntity = entityFromScene()

    scanResults = scanTextureDependency(damEntity)
    if not scanResults:
        return scanResults

    dialog = DependencyTreeDialog()

    l = ("Dependencies Status", damEntity.name, damEntity.project.name.capitalize())
    dialog.setWindowTitle(" - ".join(l))

    buttonBox = dialog.buttonBox
    okBtn = buttonBox.button(QtGui.QDialogButtonBox.Ok)

    err = None
    if "error" in scanResults[-1]["scan_severities"]:

        err = RuntimeError("Please, fix the following erros and retry publishing.")

        buttonBox.removeButton(okBtn)
        btn = buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        btn.setText("Close")

    else:
        if modal:
            okBtn.setText("Publish")

    dialog.show()
    dialog.setupTreeData(scanResults)

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
            return scanResults

    return None

