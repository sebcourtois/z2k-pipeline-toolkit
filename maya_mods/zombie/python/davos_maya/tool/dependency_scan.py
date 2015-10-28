
import os.path as osp

from PySide import QtGui
from PySide.QtCore import Qt

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import pymel.core as pm

from pytd.gui.dialogs import QuickTreeDialog
from pytd.gui.widgets import QuickTree, QuickTreeItem
#from pytd.util.logutils import logMsg
from pytaya.core.general import lsNodes
from pytd.util.fsutils import pathResolve, normCase, pathJoin

from pytd.util.strutils import labelify, assertChars
from pytd.util.qtutils import setWaitCursor
from pytd.util.sysutils import argToTuple, toStr

from davos.core.damproject import DamProject


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

class DependencyTree(QuickTree):

    def __init__(self, parent):
        super(DependencyTree, self).__init__(parent)

        QT_STYLE = QtGui.QStyleFactory.create("WindowsVista")
        self.setStyle(QT_STYLE)
        self.setAlternatingRowColors(True)

        self.itemClass = DependencyTreeItem
        self.itemClicked.connect(self.onItemClicked)

    def onItemClicked(self, item):
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
        self.resize(1100, 600)

        self.refreshBtn = self.buttonBox.addButton("Refresh", QtGui.QDialogButtonBox.ResetRole)
        self.refreshBtn.clicked.connect(self.refresh)

    def refresh(self):
        self.treeWidget.clear()
        setupTreeData(self.treeWidget, scanTextureDependency())

@setWaitCursor
def scanTextureDependency():

    sCurScnPath = pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Invalid scene name: '{}'".format(sCurScnPath))

    proj = DamProject.fromPath(sCurScnPath, fail=True)
    damAst = proj.entityFromPath(sCurScnPath, fail=True)

    proj = damAst.project
    sAstName = damAst.name
    #privTexDir = damAst.getResource("private", "texture_dir")
    sPrivTexDirPath = damAst.getPath("private", "texture_dir")
    sAllowTexTypes = proj.getVar("project", "allowed_texture_formats")

    allFileNodes = lsNodes("*", type='file', not_rn=True)
    scanResults = []
    fileNodeDct = {}

    for fileNode in allFileNodes:

        issueList = []
        sBuddyFileList = []

        sTexPath = fileNode.getAttr("fileTextureName")
        if not sTexPath:
            continue

        sAbsTexPath = pathResolve(sTexPath)

        sNormTexPath = normCase(sAbsTexPath)
        if sNormTexPath in fileNodeDct:
            fileNodeDct[sNormTexPath].append(fileNode)
            continue

        fileNodeDct[sNormTexPath] = [fileNode]

        bExists = True
        if not osp.isfile(sAbsTexPath):
            issueList.append(('FileNotFound', "error", sAbsTexPath))
            bExists = False

        sDirPath, sFilename = osp.split(sAbsTexPath)
        sBasePath, sExt = osp.splitext(sAbsTexPath)
        if sExt.lower() not in sAllowTexTypes:
            sMsg = ("Only accepts: '{}'".format("' '".join(sAllowTexTypes)))
            issueList.append(('BadTextureFormat', "error", sMsg))

        if normCase(sDirPath) != normCase(sPrivTexDirPath):
            sMsg = ("Not in '{}'".format(osp.normpath(sPrivTexDirPath)))
            issueList.append(('BadLocation', "error", sMsg))

        sMsg = ""
        sChannel = ""
        if sFilename.lower().startswith(sAstName.lower()):
            sMsg = ("Must NOT start with the asset name")
        else:
            sBaseName = osp.basename(sBasePath)
            try:
                assertChars(sBaseName, r"[\w]")
            except AssertionError, e:
                sMsg = toStr(e)
            else:
                sNameParts = sBaseName.split("_")
                if len(sNameParts) < 3:
                    sMsg = "Must have at least 3 parts: tex_subject_channel"
                elif sNameParts[0] != "tex":
                    sMsg = ("Must start with 'tex_'")
                else:
                    sChannel = sNameParts[-1]
                    if len(sChannel) not in (3, 4):
                        sMsg = ("Channel name can only have 3 or 4 characters, got '{}'"
                                .format(sChannel))
        if sMsg:
            issueList.append(('BadFilename', "error", sMsg))
            sMsg = ""

        if sExt == ".tga":

            sPsdSeverity = "error" if sChannel == "col" else "warning"
            sBuddyItems = (("psd", sPsdSeverity), ("tx", "error"))
            for sBuddyExt, sSeveriry in sBuddyItems:
                sBuddyPath = ".".join((sBasePath, sBuddyExt))
                if not osp.isfile(sBuddyPath):
                    sCode = sBuddyExt.upper() + "FileNotFound"
                    issueList.append((sCode, sSeveriry, sBuddyPath))
                else:
                    sBuddyFileList.append(sBuddyPath)

            if bExists:

                import PIL.Image
                pilimage = PIL.Image

                try:
                    tgaImg = pilimage.open(sAbsTexPath)
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
                        issueList.append(("BadTargaFormat", "error", sMsg))

                finally:
                    tgaImg.close()

        resultDct = {"abs_path":sAbsTexPath,
                     "issues":issueList,
                     "file_nodes":fileNodeDct[sNormTexPath],
                     "buddy_files":sBuddyFileList
                     }

        scanResults.append(resultDct)

    return scanResults

def setupTreeData(treeWidget, scanResults):

    sHeaderList = ["Files", "Summary", "Infos"]
    treeWidget.setHeaderLabels(sHeaderList)

    sFoundSeverities = set()
    sFileGrpItems = set()
    treeData = []
    for result in scanResults:

        fileNodes = result["file_nodes"]
        if fileNodes:

            sFileNodeNames = tuple(n.name()for n in fileNodes)

            wrappedNodes = []
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

        sAbsTexPath = result["abs_path"]
        sFilename = osp.basename(sAbsTexPath)

        issueList = result["issues"]
        if issueList:

            for sIssueCode, sSeverity, sMsg in issueList:

                sFoundSeverities.add(sSeverity)

                sSeverityTitle = (sSeverity + 's').upper()

                sItemPath = pathJoin(sSeverityTitle, labelify(sIssueCode))
                sFileGrpItems.add(sItemPath)
                sItemPath = pathJoin(sItemPath, sFilename)

                itemData = {"path": sItemPath,
                            "texts": [sFilename, sNumNodes, sMsg.strip('.')],
                            "roles":{Qt.UserRole:(0, wrappedNodes)},
                            "type":FILE_ITEM_TYPE
                            }
                treeData.append(itemData)

                for sNodeName in sFileNodeNames:
                    itemData = fileNodeTreeData[sNodeName].copy()
                    itemData["path"] = pathJoin(sItemPath, sNodeName)
                    treeData.append(itemData)
        else:
            sSeverity = "info"
            sFoundSeverities.add(sSeverity)

            sSeverityTitle = (sSeverity + 's').upper()
            sItemPath = pathJoin(sSeverityTitle, sFilename)
            sFileGrpItems.add(sSeverityTitle)

            sBuddyFileList = result["buddy_files"]

            sExtList = tuple(osp.splitext(p)[-1] for p in sBuddyFileList)
            sMsg = ", ".join(sExtList) + " found" if sBuddyFileList else ""

            itemData = {"path": sItemPath,
                        "texts": [sFilename, sNumNodes, sMsg],
                        "roles":{Qt.UserRole:(0, wrappedNodes)},
                        }
            treeData.append(itemData)

            for sPath in sBuddyFileList:

                sFilename = osp.basename(sPath)
                itemData = {"path": pathJoin(sItemPath, sFilename),
                            "texts": [sFilename, "", ""],
                            "roles":{Qt.ForegroundRole:(0, QtGui.QBrush(Qt.green))},
                            }
                treeData.append(itemData)

            for sNodeName in sFileNodeNames:
                itemData = fileNodeTreeData[sNodeName].copy()
                itemData["path"] = pathJoin(sItemPath, sNodeName)
                treeData.append(itemData)

    numCol = treeWidget.columnCount()
    for sSeverity, qtcolor in (("info", Qt.green), ("warning", Qt.yellow), ("error", Qt.red)):

        if sSeverity not in sFoundSeverities:
            continue

        color = QtGui.QColor(qtcolor)
        color.setAlpha(35)

        itemData = {"path": (sSeverity + 's').upper(),
                    #"texts": [sFilename, sNumNodes, sMsg],
                    "roles":{#Qt.ForegroundRole:(0, QtGui.QBrush(qtcolor)),
                             Qt.BackgroundRole:(xrange(numCol), QtGui.QBrush(color)), },
                    }
        treeData.insert(0, itemData)

    treeWidget.createTree(treeData)

    c = sHeaderList.index("Summary")
    for sItemPath in sFileGrpItems:
        item = treeWidget.itemFromPath(sItemPath)
        item.setText(c, "{} files".format(item.childCount()))
        #item.setExpanded(True)

    for i in xrange(treeWidget.topLevelItemCount()):
        item = treeWidget.topLevelItem(i)
        item.setExpanded(True)

def launch():

    dlg = DependencyTreeDialog()
    dlg.show()

    setupTreeData(dlg.treeWidget, scanTextureDependency())

#    dlg.close()
#    dlg.exec_()
