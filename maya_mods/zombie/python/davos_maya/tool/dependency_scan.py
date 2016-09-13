
import os
import re
from itertools import groupby

from PySide import QtGui
from PySide.QtCore import Qt

import PIL.Image
import filecmp

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import pymel.core as pm


from pytd.util.fsutils import pathResolve, normCase, pathJoin
from pytd.util.fsutils import pathReSub, pathEqual
from pytd.util.fsutils import ignorePatterns, iterPaths
from pytd.util.strutils import labelify, assertChars
from pytd.util.qtutils import setWaitCursor
from pytd.util.sysutils import argToTuple, toStr, inDevMode
from pytd.gui.dialogs import QuickTreeDialog, confirmDialog
from pytd.gui.widgets import QuickTree, QuickTreeItem
#from pytd.util.logutils import logMsg

from pytaya.core.general import lsNodes
from pytaya.core.reference import listReferences
from pytaya.core.system import iterNodeAttrFiles

from .general import infosFromScene

osp = os.path
pilimage = PIL.Image

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

        self.defaultFlags |= Qt.ItemIsEditable

        self.itemClass = DependencyTreeItem

        QT_STYLE = QtGui.QStyleFactory.create("Plastique")
        self.setStyle(QT_STYLE)
        self.setAlternatingRowColors(True)

        self.itemDelegate().setItemMarginSize(4, 4)

    def _onItemClicked(self, item):
        userData = item.data(0, Qt.UserRole)
        if userData:
            wrappedNodes = argToTuple(userData)
            pm.select(tuple(wn.node for wn in wrappedNodes))
        else:
            pm.select(cl=True)

class DependencyTreeDialog(MayaQWidgetBaseMixin, QuickTreeDialog):

    def __init__(self, scanFunc, parent=None):
        super(DependencyTreeDialog, self).__init__(parent=parent)

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setTreeWidget(DependencyTree(self))
        self.resize(900, 600)

        self.depScanDct = None
        self.__scanFunc = scanFunc

        self.refreshBtn = self.buttonBox.addButton("Refresh", QtGui.QDialogButtonBox.ResetRole)
        self.refreshBtn.clicked.connect(self.refresh)

    def refresh(self):
        self.treeWidget.clear()
        self.setupTreeData(self.__scanFunc(infosFromScene()))

    def setupTreeData(self, depScanDct, allExpanded=False):

        self.depScanDct = depScanDct
        if not depScanDct:
            return

        sAllSeveritySet = set()
        numAllPublishes = 0
        allScanResults = []
        for scanResults in depScanDct.itervalues():
            if not scanResults:
                continue
            sAllSeveritySet.update(scanResults[-1]["scan_severities"])
            numAllPublishes += scanResults[-1]["publish_count"]
            allScanResults.extend(scanResults)

        treeWidget = self.treeWidget

        sHeaderList = ["Files", "Summary", "Description"]
        treeWidget.setHeaderLabels(sHeaderList)

        sFileGrpItems = set()
        treeData = []
        for result in allScanResults:

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

                    fileAttr = fileNode.listAttr(usedAsFilename=True)[0]

                    itemData = {"texts": [sNodeName, "", fileAttr.get()],
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

        if numAllPublishes:
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


def scanReferenceFiles(proj):

    scanResults = []
    fileNodeDct = {}
    sAllSeveritySet = set()

    for oFileRef in listReferences():

        scanLogDct = {}

        sAbsPath = pathResolve(oFileRef.path)

        sNormPath = normCase(sAbsPath)
        if sNormPath in fileNodeDct:
            fileNodeDct[sNormPath].append(oFileRef)
            continue
        else:
            fileNodeDct[sNormPath] = [oFileRef]

        drcFile = None
        drcLib = proj.libraryFromPath(sAbsPath)
        if drcLib:
            drcFile = drcLib._weakFile(sAbsPath, dbNode=False)

        bExists = osp.isfile(sAbsPath)
        if not bExists:
            scanLogDct.setdefault("error", []).append(('FileNotFound', sAbsPath))

        resultDct = {"abs_path":sAbsPath,
                     "scan_log":scanLogDct,
                     "file_nodes":fileNodeDct[sNormPath],
                     "fellow_paths":[],
                     "udim_paths":[],
                     "publishable":False,
                     "drc_file":drcFile,
                     "exists":bExists,
                     }

        scanResults.append(resultDct)
        sAllSeveritySet.update(resultDct["scan_log"].iterkeys())

    if scanResults:
        scanResults[-1]["scan_severities"] = sAllSeveritySet

    return scanResults


def scanNodeAttrFiles(proj, **kwargs):

    scanResults = []
    fileNodeDct = {}
    sAllSeveritySet = set()

    sortKey = lambda i: osp.normcase(osp.dirname(i[0]))
    sSortedList = sorted(iterNodeAttrFiles(**kwargs), key=sortKey)

    for sDirPath, sAbsPathGrp in groupby(sSortedList, sortKey):

        drcLib = proj.libraryFromPath(sDirPath)

        for sAbsPath, sNodeAttr in sAbsPathGrp:

            scanLogDct = {}

            fileAttr = pm.PyNode(sNodeAttr)
            fileNode = fileAttr.node()

            sNormPath = normCase(sAbsPath)
            if sNormPath in fileNodeDct:
                fileNodeDct[sNormPath].append(fileNode)
                continue
            else:
                fileNodeDct[sNormPath] = [fileNode]

            drcFile = None
            if drcLib:
                drcFile = drcLib._weakFile(sAbsPath, dbNode=False)

            bExists = osp.isfile(sAbsPath)
            if not bExists:
                scanLogDct.setdefault("error", []).append(('FileNotFound', sAbsPath))

            resultDct = {"abs_path":sAbsPath,
                         "scan_log":scanLogDct,
                         "file_nodes":fileNodeDct[sNormPath],
                         "fellow_paths":[],
                         "udim_paths":[],
                         "publishable":False,
                         "drc_file":drcFile,
                         "exists":bExists,
                         }

            scanResults.append(resultDct)
            sAllSeveritySet.update(resultDct["scan_log"].iterkeys())

        if scanResults:
            scanResults[-1]["scan_severities"] = sAllSeveritySet

    return scanResults

UDIM_MODE = 3
UDIM_SEQ_RGX = r"\.1\d{3}\."
IMG_SEQ_RGX = r"\.0\d+\."

TGA_DEPTH_FOR_MODE = {"BGR;5": 16, "BGR":24, "BGRA":32,
                      "RGB;5": 16, "RGB":24, "RGBA":32}

def makeUdimFilePattern(p):
    return pathReSub(UDIM_SEQ_RGX, ".1???.", osp.basename(p))

def makeSequenceFilePattern(p):
    return pathReSub(IMG_SEQ_RGX, ".0*.", osp.basename(p))

@setWaitCursor
def scanTextureFiles(scnInfos, depConfDct=None):

    damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]
    sAstName = damEntity.name

    sDepType = "texture_dep"

    if not depConfDct:
        depConfDct = damEntity.getDependencyConf(sDepType, scnInfos["resource"])

    pubDepDir = depConfDct["dep_public_loc"]
    sSrcDepDirPath = depConfDct["dep_source_loc"]

    sPubDepDirPath = pubDepDir.absPath()
    if pubDepDir.exists():
        pubDepDir.loadChildDbNodes()

    sAllowedTexTypes = proj.getVar("project", "allowed_texture_formats")

    allFileNodes = lsNodes("*", type='file', not_rn=True)
    scanResults = []
    fileNodeDct = {}

    sAllSeveritySet = set()
    sFoundFileList = []
    sPrivFileList = []
    publishCount = 0
    bImgSeqSupport = False

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

        bImgSeq = fileNode.getAttr("useFrameExtension")

        sUdimPathList = []
        sTexAbsPathList = (sNodeAbsPath,)
        if bUdimMode and osp.isfile(sNodeAbsPath):
            sUdimPat = makeUdimFilePattern(sNodeAbsPath)
            sTexAbsPathList = sorted(iterPaths(osp.dirname(sNodeAbsPath), dirs=False,
                                               recursive=False,
                                               onlyFiles=ignorePatterns(sUdimPat)
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
            sBasePath, sTexExt = osp.splitext(sTexAbsPath)
            sTexExt = sTexExt.lower()

            bPublicFile = False
            sHighSeverity = "error"
            texFile = None
            bExists = osp.isfile(sTexAbsPath)

            resultDct = {"dependency_type":sDepType,
                         "abs_path":sTexAbsPath,
                         "scan_log":scanLogDct,
                         "file_nodes":fileNodeDct[sTexNormPath],
                         "fellow_paths":[],
                         "udim_paths":sUdimPathList,
                         "publishable":False,
                         "drc_file":None,
                         "exists":bExists,
                         }


            if not bExists:
                scanLogDct.setdefault("error", []).append(('FileNotFound', sTexAbsPath))
                addResult(resultDct); continue
            else:
                sFoundFileList.append(sTexNormPath)
                texFile = proj.entryFromPath(sTexAbsPath)

                resultDct["drc_file"] = texFile

                if texFile and texFile.isPublic():

                    bPublicFile = True
                    sHighSeverity = "warning"

                    scanLogDct.setdefault("info", []).append(('PublicFiles', sTexAbsPath))

                    if pathEqual(sTexDirPath, sPubDepDirPath):
                        privFile = texFile.getPrivateFile(weak=True)
                        sPrivFileList.append(normCase(privFile.absPath()))


            sFoundList = re.findall(UDIM_SEQ_RGX, sTexFilename)
            sUdimSeqExt = sFoundList[0].rstrip('.') if sFoundList else ""
            sFoundList = re.findall(IMG_SEQ_RGX, sTexFilename)
            sImgSeqExt = sFoundList[0].rstrip('.') if sFoundList else ""

            sSeqsExt = ""
            if sUdimSeqExt or sImgSeqExt:
                sBasePath = sBasePath.rsplit('.', 1)[0]
                sSeqsExt = sUdimSeqExt + sImgSeqExt

            if sUdimSeqExt:
                if not bUdimMode:
                    sMsg = "File is UDIM sequence but UDIM mode is disabled"
                    scanLogDct.setdefault(sHighSeverity, []).append(('BadUVTilingMode', sMsg))
            elif bUdimMode:
                    sMsg = "UDIM sequence must match 'name.1###.ext'"
                    scanLogDct.setdefault(sHighSeverity, []).append(('BadFilename', sMsg))

            if bImgSeqSupport:
                if sImgSeqExt:
                    if not bImgSeq:
                        sMsg = "File is Image sequence but 'Use Image Sequence' is disabled"
                        scanLogDct.setdefault(sHighSeverity, []).append(('ImageSequenceDisabled', sMsg))
                elif bImgSeq:
                    sMsg = "Image sequence must match 'name.0###.ext'"
                    scanLogDct.setdefault(sHighSeverity, []).append(('BadFilename', sMsg))
            elif sImgSeqExt:
                sMsg = "Image sequence not publishable yet"
                scanLogDct.setdefault("info", []).append(('Ignored', sMsg))
                addResult(resultDct); continue

            sBaseName = osp.basename(sBasePath)

            if sTexExt not in sAllowedTexTypes:
                sMsg = ("Only accepts: '{}'".format("' '".join(sAllowedTexTypes)))
                scanLogDct.setdefault(sHighSeverity, []).append(('BadTextureFormat', sMsg))

            if (not bPublicFile) and (not pathEqual(sTexDirPath, sSrcDepDirPath)):
                sMsg = "'{}'\n".format(osp.normpath(sTexAbsPath))
                sMsg += "NOT in '{}'".format(osp.normpath(sSrcDepDirPath))
                scanLogDct.setdefault(sHighSeverity, []).append(('BadLocation', sMsg))

            sMsg = ""
            sChannel = ""
            if sTexFilename.lower().startswith(sAstName.lower()):
                sMsg = ("Must NOT start with the asset name")
            else:
                try:
                    assertChars(sBaseName, r"[\w]")
                except ValueError as e:
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

            # list fellow (associated) files
            sFellowItems = []
            if sTexExt == ".tga":
                bColor = (sChannel == "col")
                sPsdSeverity = sHighSeverity if bColor else "info"
                sFellowItems = [(".tx", "warning"), (".psd", sPsdSeverity)]

            elif sTexExt == ".jpg":
                sFellowItems.append(("HD.jpg", "info"))

            for sFellowSufx, sBudSeverity in sFellowItems:

                sSuffix = sFellowSufx
                if sSeqsExt and ("." in sFellowSufx):
                    sSuffix = sFellowSufx.replace(".", sSeqsExt + ".")
                sFellowPath = "".join((sBasePath, sSuffix))

                if not osp.isfile(sFellowPath):
                    if not bPublicFile:
                        sFellowLabel = "".join(s.capitalize()for s in sFellowSufx.split("."))
                        sStatusCode = sFellowLabel.upper() + "FileNotFound"
                        if sBudSeverity != "info":
                            scanLogDct.setdefault(sBudSeverity, []).append((sStatusCode, sFellowPath))
                else:
                    sFoundFileList.append(normCase(sFellowPath))

                    budScanLogDct = {}
                    budFile = proj.entryFromPath(sFellowPath)
                    if budFile and budFile.isPublic():

                        budScanLogDct.setdefault("info", []).append(('PublicFiles', sFellowPath))

                        if pathEqual(osp.dirname(sFellowPath), sPubDepDirPath):
                            privBudFile = budFile.getPrivateFile(weak=True)
                            sPrivFileList.append(normCase(privBudFile.absPath()))

                    budResultDct = {"dependency_type":sDepType,
                                    "abs_path":sFellowPath,
                                    "scan_log":budScanLogDct,
                                    "file_nodes":[],
                                    "fellow_paths":[],
                                    "udim_paths":[],
                                    "publishable":False,
                                    "drc_file":budFile,
                                    "exists":True,
                                    }
                    foundBudResList.append(budResultDct)

            # targa format check
            if sTexExt == ".tga" and (not bPublicFile):
                tgaImg = None
                try:
                    tgaImg = pilimage.open(sTexAbsPath)
                    tileInfo = tgaImg.tile[0]
                    sCompress = tileInfo[0]
                    sMode = tileInfo[-1][0]

                    if sMode not in TGA_DEPTH_FOR_MODE:
                        sMsg = ("Invalid mode: '{}'. Valid modes: {}"
                                .format(sMode, TGA_DEPTH_FOR_MODE.keys()))
                        raise ValueError(sMsg)

                    sMsgList = []
                    bRgb24 = (sMode == "BGR")
                    bCompr = (sCompress == "tga_rle")

                    if not bRgb24:
                        sMsg = "Expected 24 bits, got {} bits".format(TGA_DEPTH_FOR_MODE[sMode])
                        sMsgList.append(sMsg)

                    if not bCompr:
                        sMsgList.append("NOT COMPRESSED")

                    if sMsgList:
                        sMsg = "\n".join(sMsgList)
                        scanLogDct.setdefault(sHighSeverity, []).append(("BadTargaFormat", sMsg))

                except Exception as e:
                    scanLogDct.setdefault(sHighSeverity, []).append(("BadTargaFormat", toStr(e)))
                finally:
                    if tgaImg:
                        tgaImg.close()

            resultDctList = [resultDct]
            if foundBudResList:
                resultDctList.extend(foundBudResList)
                sFellowFileList = list(d["abs_path"] for d in foundBudResList)
                resultDct["fellow_paths"] = sFellowFileList

            for resDct in resultDctList:
                if resDct["exists"]:
                    _setPublishableState(resDct)
                    if resDct["publishable"]:
                        publishCount += 1
                addResult(resDct)

    sAllowedFileTypes = [".tx", ".psd"]
    sAllowedFileTypes.extend(sAllowedTexTypes)
    #looking for unused files in texture direcotry
    if osp.isdir(sSrcDepDirPath):

        sTexDirFileList = sorted(iterPaths(sSrcDepDirPath, dirs=False, recursive=False))

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

            resultDct = {"dependency_type":sDepType,
                         "abs_path":p,
                         "scan_log":scanLogDct,
                         "file_nodes":[],
                         "fellow_paths":[],
                         "udim_paths":[],
                         "publishable":False,
                         "drc_file":None,
                         }
            addResult(resultDct)

    if scanResults:
        scanResults[-1]["scan_severities"] = sAllSeveritySet
        scanResults[-1]["publish_count"] = publishCount

    return scanResults

@setWaitCursor
def scanAlembicFiles(scnInfos, depConfDct=None):

    damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]
    pubLib = damEntity.getLibrary("public")

    sDepType = "geoCache_dep"
    if not depConfDct:
        depConfDct = damEntity.getDependencyConf(sDepType, scnInfos["resource"])
    pubDepDir = depConfDct["dep_public_loc"]
    sSrcDepDirPath = depConfDct["dep_source_loc"]

    sPubDepDirPath = pubDepDir.absPath()
    if pubDepDir.exists():
        pubDepDir.loadChildDbNodes()

    scanResults = []
    fileNodeDct = {}

    sAllSeveritySet = set()

    def addResult(res):
        scanResults.append(res)
        sAllSeveritySet.update(res["scan_log"].iterkeys())

    def iterAlembicPaths():

        allFileNodes = lsNodes("*", type='AlembicNode', not_rn=True)

        for fileNode in allFileNodes:

            sAbcPath = fileNode.getAttr("abc_File")
            if not sAbcPath:
                continue

            sDepAbsPath = pathResolve(sAbcPath)
            sDepNormPath = normCase(sDepAbsPath)

            if sDepNormPath in fileNodeDct:
                fileNodeDct[sDepNormPath].append(fileNode)
                continue
            else:
                fileNodeDct[sDepNormPath] = [fileNode]

            yield sDepAbsPath

    def doScan(sAllDepPathList):

        for sDepAbsPath in sAllDepPathList:

            sDepNormPath = normCase(sDepAbsPath)
            scanLogDct = {}

            sHighSeverity = "error"
            bPublicFile = False
            bExists = osp.isfile(sDepAbsPath)

            resultDct = {"dependency_type":sDepType,
                         "abs_path":sDepAbsPath,
                         "scan_log":scanLogDct,
                         "file_nodes":fileNodeDct.get(sDepNormPath, []),
                         "fellow_paths":[],
                         "publishable":False,
                         "drc_file":None,
                         "exists":bExists,
                         "public_file":None,
                        }

            sDepDirPath, sDepFilename = osp.split(sDepAbsPath)

            if not bExists:
                scanLogDct.setdefault("error", []).append(('FileNotFound', sDepAbsPath))
                addResult(resultDct); continue

            abcFile = proj.entryFromPath(sDepAbsPath, dbNode=False)
            resultDct["drc_file"] = abcFile

            if abcFile and abcFile.isPublic():
                bPublicFile = True
                sHighSeverity = "warning"
                scanLogDct.setdefault("info", []).append(('PublicFiles', sDepAbsPath))
                resultDct["public_file"] = abcFile
            else:
                sDepPubPath = pathJoin(sPubDepDirPath, sDepFilename)
                resultDct["public_file"] = pubLib._weakFile(sDepPubPath, dbNode=False)

            if (not bPublicFile) and (not pathEqual(sDepDirPath, sSrcDepDirPath)):
                sMsg = "'{}'\n".format(osp.normpath(sDepAbsPath))
                sMsg += "NOT in '{}'".format(osp.normpath(sSrcDepDirPath))
                scanLogDct.setdefault(sHighSeverity, []).append(('BadLocation', sMsg))

            _setPublishableState(resultDct)
            addResult(resultDct)

    doScan(iterAlembicPaths())

    publishCount = sum(1 for d in scanResults if d["publishable"])
    if publishCount:
        sAbcJsonPath = pathJoin(sSrcDepDirPath, "abcExport.json")
        doScan([sAbcJsonPath])

    if scanResults:
        scanResults[-1]["scan_severities"] = sAllSeveritySet
        scanResults[-1]["publish_count"] = publishCount

    return scanResults

def _setPublishableState(resultDct):

    scanLogDct = resultDct["scan_log"]
    if "error" in scanLogDct:
        return

    drcFile = resultDct["drc_file"]

    if drcFile:
        if drcFile.isPublic():
            return False
        pubFile = drcFile.getPublicFile(weak=True, dbNode=False)
    else:
        pubFile = resultDct.get("public_file")
        if not pubFile:
            return False

    bPublishable = True
    sPubFilePath = pubFile.absPath()

    dbNode = pubFile.loadDbNode(fromDb=False)
    if dbNode:
        pubFile.refresh(simple=True)
    else:
        dbNode = pubFile.loadDbNode(fromCache=False)

    sSrcFilePath = resultDct["abs_path"]
    if pubFile.exists():
        try:
            pubFile._assertPublishable(sSrcFilePath, refresh=False)
        except EnvironmentError as e:
            bPublishable = False
            sErrMsg = toStr(e)
    elif dbNode:
        sErrMsg = """File declared in database but does not exist on your server.
Wait for the next synchro and retry publishing."""
        bPublishable = False

    if not bPublishable:
        scanLogDct.setdefault("error", []).append(("NotPublishable", sErrMsg))
    else:
        bModified = True
        if pubFile.exists():
            bModified = (not filecmp.cmp(sSrcFilePath, sPubFilePath))
            #bDiffers, sSrcChecksum = pubFile.differsFrom(sPubFilePath)

        if not bModified:
            scanLogDct.setdefault("info", []).append(("NotModified", "File has not been modified"))
        else:
            sMsg = ""
            sFellowFileList = resultDct["fellow_paths"]
            if sFellowFileList:
                sExtList = tuple(osp.basename(p).split(pubFile.baseName, 1)[-1]
                                 for p in sFellowFileList)
                sMsg = (", ".join(s.upper() for s in sExtList) + " found"
                        if sFellowFileList else "")
            elif inDevMode():
                sMsg = resultDct["abs_path"]

            scanLogDct.setdefault("info", []).append(("ReadyToPublish", sMsg))

    resultDct["publishable"] = bPublishable

    return bPublishable

def scanAllDependencyTypes(scnInfos):

    proj = scnInfos["project"]
    sSection = scnInfos["section"]
    sRcName = scnInfos["resource"]

    depScanDct = {}
    for sDepType in proj.getDependencyTypes(sSection, sRcName).iterkeys():
        scanResults = None
        if sDepType == "texture_dep":
            scanResults = scanTextureFiles(scnInfos)
        elif sDepType == "geoCache_dep":
            scanResults = scanAlembicFiles(scnInfos)
        else:
            pm.displayWarning("Dependency type NOT supported yet: '{}'"
                              .format(sDepType))
        if scanResults:
            depScanDct[sDepType] = scanResults

    return depScanDct

dialog = None

def launch(scnInfos=None, scanFunc=None, modal=False, okLabel="OK",
           expandTree=False, forceDialog=False):

    global dialog

    if not scnInfos:
        scnInfos = infosFromScene()

    damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]

    if scanFunc is None:
        scanFunc = scanAllDependencyTypes

    depScanDct = scanFunc(scnInfos)
    if not depScanDct:
        return depScanDct

    sAllSeveritySet = set()
    for scanResults in depScanDct.itervalues():
        if not scanResults:
            continue
        sAllSeveritySet.update(scanResults[-1]["scan_severities"])

    if (not forceDialog) and (not sAllSeveritySet):
        return depScanDct

    dialog = DependencyTreeDialog(scanFunc)

    l = ("Dependencies Status", damEntity.name, proj.name.capitalize())
    dialog.setWindowTitle(" - ".join(l))

    buttonBox = dialog.buttonBox
    okBtn = buttonBox.button(QtGui.QDialogButtonBox.Ok)

    err = None
    if "error" in sAllSeveritySet:

        err = RuntimeError("Please, fix the following errors and retry...")

        buttonBox.removeButton(okBtn)
        btn = buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        btn.setText("Close")
    else:
        if modal:
            okBtn.setText(okLabel)

    dialog.show()
    dialog.setupTreeData(depScanDct, allExpanded=expandTree)

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
            return dialog.depScanDct

    return None

