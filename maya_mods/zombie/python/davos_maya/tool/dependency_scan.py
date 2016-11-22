
import os
import re
import glob
import functools
from itertools import groupby
from pprint import pprint
#import filecmp


from PySide import QtGui
from PySide.QtCore import Qt

import PIL.Image

import pymel.core as pm

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

from pytd.util.fsutils import normCase, pathJoin, pathNorm, pathNormAll
from pytd.util.fsutils import pathResolve, pathReSub, pathEqual
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
from davos.core.utils import isPack
from davos.core.damtypes import DamShot

osp = os.path
pilimage = PIL.Image

mainWin = None

FILE_ITEM_TYPE = 1000
NODE_ITEM_TYPE = FILE_ITEM_TYPE + 1

FILE_PATH_ATTRS = {
"file":"fileTextureName",
"AlembicNode":"abc_File",
"cacheFile":"cachePath",
"BE_VDBRead":"VdbFilePath",
"BE_VDBArnoldRender":"volumePath",
}


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
            sFileNodeList = tuple(n.name()for n in fileNodes)

            wrappedNodes = []
            numNodes = 0
            sNumNodes = ""

            if fileNodes:
                fileNodeTreeData = {}
                for fileNode in fileNodes:

                    sNodeName = fileNode.name()

                    wrappedNode = WrappedNode(fileNode)
                    wrappedNodes.append(wrappedNode)

                    fileAttr = fileNode.attr(FILE_PATH_ATTRS[fileNode.type()])

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

                    for sNodeName in sFileNodeList:
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

        sNormPath = pathNormAll(sAbsPath)
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

            sNormPath = pathNormAll(sAbsPath)
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
UDIM_REXP = r"\.1\d{3}\."
FRAME_REXP = r"\.\d+\."

TGA_DEPTH_FOR_MODE = {"BGR;5": 16, "BGR":24, "BGRA":32,
                      "RGB;5": 16, "RGB":24, "RGBA":32}

def _mkUdimFilePattern(p):
    return pathReSub(UDIM_REXP, ".1???.", osp.basename(p))

def _mkSeqFilePattern(p):
    return pathReSub(FRAME_REXP, ".*.", osp.basename(p))

def _getSeqExts(sTexName):
    sFoundList = re.findall(UDIM_REXP, sTexName)
    sUdimExt = sFoundList[0].rstrip('.') if sFoundList else ""
    if sUdimExt:
        sTexName = sTexName.replace(sUdimExt, "")
    sFoundList = re.findall(FRAME_REXP, sTexName)
    sFrameExt = sFoundList[0].rstrip('.') if sFoundList else ""
    return sUdimExt, sFrameExt

@setWaitCursor
def scanTextureFiles(scnInfos, depConfDct=None):

    damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]

    sDepType = "texture_dep"

    if not depConfDct:
        depConfDct = damEntity.getDependencyConf(sDepType, scnInfos["resource"])

    pubDepDir = depConfDct["dep_public_loc"]
    sSrcDepDirPath = depConfDct["dep_source_loc"]

    sPubDepDirPath = pubDepDir.absPath()
    if pubDepDir.exists():
        pubDepDir.loadChildDbNodes(recursive=True)

    sAllowedTexTypes = proj.getVar("project", "allowed_texture_formats")

    allFileNodes = lsNodes("*", type='file', not_rn=True)
    scanResults = []
    fileNodeDct = {}

    sAllSeveritySet = set()
    sFoundFileList = []
    sPrivFileList = []

    for fileNode in allFileNodes:

        sOnNodePath = fileNode.getAttr("fileTextureName")
        if not sOnNodePath:
            continue

        sOnNodeAbsPath = pathNorm(pathResolve(sOnNodePath))
        sOnNodeNormPath = pathNormAll(sOnNodeAbsPath)

        iTilingMode = fileNode.getAttr("uvTilingMode")
        bUvTileOn = (iTilingMode != 0)
        bUdimMode = (iTilingMode == UDIM_MODE)
        bUseFrame = fileNode.getAttr("useFrameExtension")

        sUdimPathList = []
        sTexAbsPathList = [sOnNodeAbsPath]

        if osp.isfile(sOnNodeAbsPath):
            if bUdimMode:
                sPatrn = _mkUdimFilePattern(sOnNodeAbsPath)
                sTexAbsPathList = sorted(iterPaths(osp.dirname(sOnNodeAbsPath),
                                                   dirs=False, recursive=False,
                                                   onlyFiles=ignorePatterns(sPatrn)
                                                   ))
                sUdimPathList = sTexAbsPathList[:]
#            elif bUseFrame:
#                sPatrn = _mkSeqFilePattern(sOnNodeAbsPath)
#                sTexAbsPathList = sorted(iterPaths(osp.dirname(sOnNodeAbsPath),
#                                                   dirs=False, recursive=False,
#                                                   onlyFiles=ignorePatterns(sPatrn)
#                                                   ))
#                sUdimPathList = sTexAbsPathList[:]

        for sTexAbsPath in sTexAbsPathList:

            scanLogDct = {}
            resultDct = {}
            foundBudResList = []

            sTexNormPath = pathNormAll(sTexAbsPath)
            bPathOnNode = (sTexNormPath == sOnNodeNormPath)
            if sTexNormPath in fileNodeDct:
                if bPathOnNode:
                    fileNodeDct[sTexNormPath].append(fileNode)
                continue
            else:
                fileNodeDct[sTexNormPath] = [fileNode] if bPathOnNode else []

            if bUvTileOn and (not bUdimMode):
                sMsg = "Only UDIM (Mari) supported"
                scanLogDct.setdefault("error", []).append(('BadUVTilingMode', sMsg))

            sTexDirPath, sTexFilename = osp.split(sTexAbsPath)
            sBasePath, sTexExt = osp.splitext(sTexAbsPath)
            sTexExt = sTexExt.lower()

            bPublicFile = False
            sHighSeverity = "error"
            rcFile = proj.entryFromPath(sTexAbsPath, dbNode=False)
            if rcFile:
                bExists = True
                if rcFile.isPublic():
                    bPublicFile = True
                    sHighSeverity = "warning"
            else:
                bExists = osp.isfile(sTexAbsPath)

            if bExists:
                sFoundFileList.append(sTexNormPath)

            resultDct = {"dependency_type":sDepType,
                         "abs_path":sTexAbsPath,
                         "scan_log":scanLogDct,
                         "file_nodes":fileNodeDct[sTexNormPath],
                         "fellow_paths":[],
                         "udim_paths":sUdimPathList,
                         "publishable":False,
                         "drc_file":rcFile,
                         "exists":bExists,
                         "public_file":None,
                         }

            if not bExists:
                scanLogDct.setdefault("error", []).append(('FileNotFound',
                                                           sTexAbsPath))
                scanResults.append(resultDct); continue

            sUdimExt, sFrameExt = _getSeqExts(sTexFilename)

            bInPack = isPack(sTexDirPath)
            if sFrameExt and bUseFrame:
                if (not bInPack):
                    if pathEqual(sTexDirPath, sSrcDepDirPath):
                        sMsg = "Add image sequence to a package folder (starts with 'pkg_')"
                    else:
                        sMsg = "Image sequence is NOT in a package.\n"
                        sMsg += "Rename '{}' folder so it starts with 'pkg_'"
                        sMsg = sMsg.format(osp.basename(sTexDirPath))

                    scanLogDct.setdefault("error", []).append(('BadLocation', sMsg))

                    scanResults.append(resultDct); continue
                else:
                    resultDct["pack_path"] = sTexDirPath
            elif (not sFrameExt) and bInPack:
                sMsg = ("Single texture file found in a package folder: '{}'.\n"
                        .format(osp.basename(sTexDirPath)))
                sMsg += "Package is intended to publish image sequence."
                scanLogDct.setdefault("error", []).append(('BadLocation', sMsg))

            if bPublicFile:
                scanLogDct.setdefault("info", []).append(('PublicFile',
                                                          sTexAbsPath))
                if pathEqual(sTexDirPath, sPubDepDirPath):
                    privFile = rcFile.getPrivateFile(weak=True)
                    sPrivFileList.append(normCase(privFile.absPath()))

            if bInPack:
                sTexDirPath = osp.dirname(sTexDirPath)

            sSeqExts = ""
            if sUdimExt or sFrameExt:
                sBasePath = sBasePath.rsplit('.', 1)[0]
                sSeqExts = sUdimExt + sFrameExt

            if sUdimExt:
                if not bUdimMode:
                    sMsg = "File is UDIM sequence but UDIM mode is disabled"
                    scanLogDct.setdefault(sHighSeverity, []).append(('BadUVTilingMode', sMsg))
            elif bUdimMode:
                    sMsg = "UDIM sequence must match 'name.1###.ext'"
                    scanLogDct.setdefault(sHighSeverity, []).append(('BadFilename', sMsg))

            if sFrameExt and not bUseFrame:
                sMsg = ("Has frame extension ('{}') but 'Use Image Sequence' disabled"
                        .format(sFrameExt))
                scanLogDct.setdefault(sHighSeverity, []).append(('UnusedImageSequence', sMsg))

            if sTexExt not in sAllowedTexTypes:
                sMsg = ("Only accepts: '{}'".format("' '".join(sAllowedTexTypes)))
                scanLogDct.setdefault(sHighSeverity, []).append(('BadTextureFormat', sMsg))

            if sSrcDepDirPath and (not bPublicFile) and (not pathEqual(sTexDirPath, sSrcDepDirPath)):
                sMsg = "'{}'\n".format(osp.normpath(sTexAbsPath))
                sMsg += "NOT in '{}'".format(osp.normpath(sSrcDepDirPath))
                scanLogDct.setdefault(sHighSeverity, []).append(('BadLocation', sMsg))

            sBaseName = osp.basename(sBasePath)
            sChannel, logItems = _checkTextureBaseName(damEntity, sBaseName)
            if logItems and (not bPublicFile):
                scanLogDct.setdefault(sHighSeverity, []).append(logItems)

            # list fellow (associated) files
            sFellowItems = []
            if not sFrameExt:
                if sTexExt == ".tga":
                    bColor = (sChannel == "col")
                    sPsdSeverity = sHighSeverity if bColor else "info"
                    sFellowItems = [(".tx", "warning"), (".psd", sPsdSeverity)]

                elif sTexExt == ".jpg":
                    sFellowItems.append(("HD.jpg", "info"))

            for sFellowSufx, sFellowSever in sFellowItems:

                sSuffix = sFellowSufx
                if sSeqExts and ("." in sFellowSufx):
                    sSuffix = sFellowSufx.replace(".", sSeqExts + ".")
                sFellowPath = "".join((sBasePath, sSuffix))

                if not osp.isfile(sFellowPath):
                    if not bPublicFile:
                        sFellowLabel = "".join(s.capitalize()for s in sFellowSufx.split("."))
                        sStatusCode = sFellowLabel.upper() + "FileNotFound"
                        if sFellowSever != "info":
                            scanLogDct.setdefault(sFellowSever, []).append((sStatusCode, sFellowPath))
                else:
                    sFoundFileList.append(pathNormAll(sFellowPath))

                    budScanLogDct = {}
                    budFile = proj.entryFromPath(sFellowPath, dbNode=False)
                    if budFile and budFile.isPublic():

                        budScanLogDct.setdefault("info", []).append(('PublicFile', sFellowPath))

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

            resultList = [resultDct]
            if foundBudResList:
                resultList.extend(foundBudResList)
                sFellowFileList = list(d["abs_path"] for d in foundBudResList)
                resultDct["fellow_paths"] = sFellowFileList

            for res in resultList:
                scanResults.append(res)

    publishCount = setPublishableStates(scanResults, pubDepDir)

#    sAllowedFileTypes = [".tx", ".psd"]
#    sAllowedFileTypes.extend(sAllowedTexTypes)
#    #looking for unused files in texture direcotry
#    if osp.isdir(sSrcDepDirPath):
#
#        sTexDirFileList = sorted(iterPaths(sSrcDepDirPath, dirs=False, recursive=False))
#
#        for p in sTexDirFileList:
#
#            print p
#
#            scanLogDct = {}
#
#            sExt = osp.splitext(p)[-1]
#            if sExt.lower() not in sAllowedFileTypes:
#                continue
#
#            np = normCase(p)
#            if np in sPrivFileList:
#                pass#scanLogDct.setdefault("info", []).append(("AlreadyPublished", p))
#            elif np not in sFoundFileList:
#                scanLogDct.setdefault("warning", []).append(("UnusedPrivateFiles", p))
#            else:
#                continue
#
#            resultDct = {"dependency_type":sDepType,
#                         "abs_path":p,
#                         "scan_log":scanLogDct,
#                         "file_nodes":[],
#                         "fellow_paths":[],
#                         "udim_paths":[],
#                         "publishable":False,
#                         "drc_file":None,
#                         }
#            scanResults.append(resultDct)

    if scanResults:

        for res in scanResults:
            sAllSeveritySet.update(res["scan_log"].iterkeys())

        scanResults[-1]["scan_severities"] = sAllSeveritySet
        scanResults[-1]["publish_count"] = publishCount

    return scanResults

def _checkTextureBaseName(damEntity, sBaseName):

    sAstName = damEntity.name

    sMsg = ""
    sChannel = ""
    if sBaseName.lower().startswith(sAstName.lower()):
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

    return sChannel, ('BadFilename', sMsg) if sMsg else None

def firstPrefix(sNodeName):
    return sNodeName.split("_", 1)[0] if "_" in sNodeName else ""

@setWaitCursor
def scanGeoCacheFiles(scnInfos, depConfDct=None):

    damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]
    #pubLib = damEntity.getLibrary("public")

    sGeoAstTypeList = list(proj.iterAssetPrefixes())
    sGeoAstTypeList.remove("fxp")

    sDepType = "geoCache_dep"
    if not depConfDct:
        depConfDct = damEntity.getDependencyConf(sDepType, scnInfos["resource"])
    pubDepDir = depConfDct["dep_public_loc"]
    sSrcDepDirPath = depConfDct["dep_source_loc"]

    #sPubDepDirPath = pubDepDir.absPath()
    if pubDepDir.exists():
        pubDepDir.loadChildDbNodes()

    scanResults = []
    fileNodeDct = {}

    sAllSeveritySet = set()

    def addResult(res):
        scanResults.append(res)
        sAllSeveritySet.update(res["scan_log"].iterkeys())

    def iterAlembicPaths():

        sIgnorePathList = []
        if isinstance(damEntity, DamShot):
            sIgnorePathList.append(damEntity.getPath("public", "camera_abc"))
            sIgnorePathList.append(damEntity.getPath("private", "camera_abc"))

        allFileNodes = lsNodes("*", type='AlembicNode', not_rn=True)

        for fileNode in allFileNodes:

            sAbcPath = fileNode.getAttr("abc_File")
            if not sAbcPath:
                continue

            sDepAbsPath = pathNorm(pathResolve(sAbcPath))
            sDepNormPath = pathNormAll(sDepAbsPath)

            if sIgnorePathList and sDepNormPath in sIgnorePathList:
                continue

            sFileName = osp.basename(sDepNormPath)
            if firstPrefix(sFileName) not in sGeoAstTypeList:
                continue

            if sDepNormPath in fileNodeDct:
                fileNodeDct[sDepNormPath].append(fileNode)
                continue
            else:
                fileNodeDct[sDepNormPath] = [fileNode]

            yield sDepAbsPath

    def doScan(sAllDepPathList):

        for sDepAbsPath in sAllDepPathList:

            sDepNormPath = pathNormAll(sDepAbsPath)
            scanLogDct = {}

            bExists = False
            bPublicFile = False
            sHighSeverity = "error"
            rcFile = proj.entryFromPath(sDepAbsPath, dbNode=False)
            if rcFile:
                bExists = True
                if rcFile.isPublic():
                    bPublicFile = True
                    sHighSeverity = "warning"
            elif not bExists:
                bExists = osp.isfile(sDepAbsPath)

            resultDct = {"dependency_type":sDepType,
                         "abs_path":sDepAbsPath,
                         "scan_log":scanLogDct,
                         "file_nodes":fileNodeDct.get(sDepNormPath, []),
                         "fellow_paths":[],
                         "publishable":False,
                         "drc_file":rcFile,
                         "exists":bExists,
                         "public_file":None,
                        }

            sDepDirPath, sDepFilename = osp.split(sDepAbsPath)

            if bPublicFile:
                scanLogDct.setdefault("info", []).append(('PublicFile', sDepAbsPath))
                addResult(resultDct); continue

            if not bExists:
                scanLogDct.setdefault("error", []).append(('FileNotFound', sDepAbsPath))
                addResult(resultDct); continue

            if (not bPublicFile) and (not pathEqual(sDepDirPath, sSrcDepDirPath)):
                sMsg = "'{}'\n".format(osp.normpath(sDepAbsPath))
                sMsg += "NOT in '{}'".format(osp.normpath(sSrcDepDirPath))
                scanLogDct.setdefault(sHighSeverity, []).append(('BadLocation', sMsg))

            #_loadPublicFile(resultDct, pubDepDir)
            #_setPublishableState(resultDct)

            addResult(resultDct)

    doScan(iterAlembicPaths())

    publishCount = setPublishableStates(scanResults, pubDepDir)#sum(1 for d in scanResults if d["publishable"])
    if publishCount:
        sAbcJsonPath = pathJoin(sSrcDepDirPath, "abcExport.json")
        doScan([sAbcJsonPath])
        c = setPublishableStates(scanResults[-1:], pubDepDir, loadDbNodes=False)
        if c:
            publishCount += c

    if scanResults:
        scanResults[-1]["scan_severities"] = sAllSeveritySet
        scanResults[-1]["publish_count"] = publishCount

    return scanResults

@setWaitCursor
def scanFxCacheFiles(scnInfos, depConfDct=None):

    damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]
    #pubLib = damEntity.getLibrary("public")

    sGeoAstTypeList = list(proj.iterAssetPrefixes())
    sGeoAstTypeList.remove("fxp")

    sDepType = "fxCache_dep"
    if not depConfDct:
        depConfDct = damEntity.getDependencyConf(sDepType, scnInfos["resource"])
    pubDepDir = depConfDct["dep_public_loc"]

    #sPubDepDirPath = pubDepDir.absPath()
    if pubDepDir.exists():
        pubDepDir.loadChildDbNodes()

    scanResults = []
    fileNodeDct = {}

    sAllSeveritySet = set()

    def addResult(res):
        scanResults.append(res)
        #sAllSeveritySet.update(res["scan_log"].iterkeys())

    def iterCachePaths(sNodeType, pathFromNodeFnc=None, ignorePaths=None):

        sFileAttrName = FILE_PATH_ATTRS[sNodeType]
        allFileNodes = lsNodes("*", type=sNodeType, not_rn=True)

        sIgnorePathList = None
        if ignorePaths:
            sIgnorePathList = tuple(pathNormAll(p) for p in ignorePaths)

        for fileNode in allFileNodes:

            if pathFromNodeFnc:
                res = pathFromNodeFnc(fileNode)
                if isinstance(res, list):
                    sDepPath = res[0]
                    for p in res[1:]:
                        yield pathNorm(pathResolve(p))
                else:
                    sDepPath = res
            else:
                sDepPath = fileNode.getAttr(sFileAttrName)

            if not sDepPath:
                continue

            sDepAbsPath = pathNorm(pathResolve(sDepPath))
            sDepNormPath = pathNormAll(sDepAbsPath)

            if sIgnorePathList and (sDepNormPath in sIgnorePathList):
                continue

            sFileName = osp.basename(sDepNormPath)
            if firstPrefix(sFileName) in sGeoAstTypeList:
                continue

            if sDepNormPath in fileNodeDct:
                fileNodeDct[sDepNormPath].append(fileNode)
                continue
            else:
                fileNodeDct[sDepNormPath] = [fileNode]

            yield sDepAbsPath

    def doScan(sAllDepPathList):

        for sDepAbsPath in sAllDepPathList:

            sDepNormPath = pathNormAll(sDepAbsPath)
            scanLogDct = {}

            fileNodeList = fileNodeDct.get(sDepNormPath, [])

            bExists = False
            bFileSeq = False

            if fileNodeList:
                fileNode = fileNodeList[0]
                sNodeType = fileNode.type()
                if sNodeType == "cacheFile":
                    bFileSeq = fileNode.useFileSequence
                elif sNodeType in ("BE_VDBRead", "BE_VDBArnoldRender"):
                    if ("#" in sDepAbsPath):
                        bFileSeq = True
                        sFileList = sorted(glob.iglob(sDepAbsPath.replace("#", "?")))
                        if sFileList:
                            sDepAbsPath = pathNorm(sFileList[0])
                            bExists = True

            bPublicFile = False
            sHighSeverity = "error"
            rcFile = proj.entryFromPath(sDepAbsPath, dbNode=False)
            if rcFile:
                bExists = True
                if rcFile.isPublic():
                    bPublicFile = True
                    sHighSeverity = "warning"
            elif not bExists:
                bExists = osp.isfile(sDepAbsPath)

            resultDct = {"dependency_type":sDepType,
                         "abs_path":sDepAbsPath,
                         "scan_log":scanLogDct,
                         "file_nodes":fileNodeList,
                         "fellow_paths":[],
                         "publishable":False,
                         "drc_file":rcFile,
                         "exists":bExists,
                         "public_file":None,
                        }

            sDepDirPath, sDepFilename = osp.split(sDepAbsPath)

            if bPublicFile:
                scanLogDct.setdefault("info", []).append(('PublicFile', sDepAbsPath))
                #addResult(resultDct); continue

            if not bExists:
                scanLogDct.setdefault("error", []).append(('FileNotFound', sDepAbsPath))
                addResult(resultDct); continue

            bInPack = isPack(sDepDirPath)
            if bFileSeq:
                if (not bInPack):
                    sMsg = "Cache sequence is NOT in a package.\n"
                    sMsg += "Rename '{}' folder so it starts with 'pkg_'"
                    sMsg = sMsg.format(osp.basename(sDepDirPath))
                    scanLogDct.setdefault(sHighSeverity, []).append(('BadLocation', sMsg))
                    scanResults.append(resultDct); continue
                else:
                    resultDct["pack_path"] = sDepDirPath
            elif bInPack:
                sMsg = ("Single cache file found in a package folder: '{}'.\n"
                        .format(osp.basename(sDepDirPath)))
                sMsg += "Package is intended to publish image sequence."
                scanLogDct.setdefault(sHighSeverity, []).append(('BadLocation', sMsg))

#            pubDepFile = proj.entryFromPath(sDepAbsPath, dbNode=False)
#            resultDct["drc_file"] = pubDepFile

#            print "\n", sDepNormPath
#            print sPubDepDirPath

            addResult(resultDct)

    sIgnorePathList = []
    if isinstance(damEntity, DamShot):
        sIgnorePathList.append(damEntity.getPath("public", "camera_abc"))
        sIgnorePathList.append(damEntity.getPath("private", "camera_abc"))

    doScan(iterCachePaths("AlembicNode", ignorePaths=sIgnorePathList))

    def pathFromCacheNode(cacheNode):
        cacheNode.useFileSequence = False
        sFileList = pm.cacheFile(cacheNode, q=True, fileName=True)
        if not sFileList:
            return pathJoin(cacheNode.getAttr("cachePath"), cacheNode.getAttr("cacheName") + ".xml")
        if len(sFileList) > 2:
            cacheNode.useFileSequence = True
            return sFileList[0]
        else:
            return sFileList

    doScan(iterCachePaths("cacheFile", pathFromCacheNode))

    doScan(iterCachePaths("BE_VDBRead"))

    pathFromNode = lambda n: n.getAttr("volumePath") if n.getAttr("FromFile") else ""
    doScan(iterCachePaths("BE_VDBArnoldRender", pathFromNode))

    publishCount = setPublishableStates(scanResults, pubDepDir)

    if scanResults:

        for res in scanResults:
            sAllSeveritySet.update(res["scan_log"].iterkeys())

        scanResults[-1]["scan_severities"] = sAllSeveritySet
        scanResults[-1]["publish_count"] = publishCount

    return scanResults

def _loadPublicFile(resultDct, pubDepDir):

    rcFile = resultDct["drc_file"]
    if rcFile and rcFile.isPublic():
        pubFile = rcFile
    else:
        sBaseName = osp.basename(pathNorm(resultDct["abs_path"]))
        pubFile = pubDepDir.getChildFile(sBaseName, weak=True, dbNode=False)

    resultDct["public_file"] = pubFile
    return pubFile

def setPublishableStates(scanResults, pubDepDir, loadDbNodes=True):

    proj = pubDepDir.library.project

    if loadDbNodes and pubDepDir.exists():
        pubDepDir.loadChildDbNodes(recursive=True)

    pubFileDct = {}
    publishCount = 0
    sPackPathList = []
    for res in scanResults:

        if not res["exists"]:
            continue

        sPackPath = res.get("pack_path")
        if sPackPath:

            sPackNormPath = pathNormAll(sPackPath)
            if sPackNormPath in sPackPathList:
                continue

            res["abs_path"] = sPackPath
            res["drc_file"] = proj.entryFromPath(sPackPath, dbNode=False)
            sPackPathList.append(sPackNormPath)

        bIgnore = False
        pubFile = _loadPublicFile(res, pubDepDir)
        if res["drc_file"] != pubFile:
            if pubFile in pubFileDct:
                scanLogDct = res["scan_log"]
                sErrMsg = ("'{}' used to publish:\n - {}"
                           .format(pubFile.name, pubFileDct[pubFile]["abs_path"]))
                scanLogDct.setdefault("error", []).append(("NameAlreadyUsed", sErrMsg))
                bIgnore = True

        pubFileDct[pubFile] = res

        if bIgnore:
            continue

        _setPublishableState(res, refreshDbNode=False)

        if res["publishable"]:
            publishCount += 1

    return publishCount

def _setPublishableState(resultDct, refreshDbNode=True):

    scanLogDct = resultDct["scan_log"]
    if "error" in scanLogDct:
        return

    rcFile = resultDct["drc_file"]
    if rcFile and rcFile.isPublic():
        return False

    pubFile = resultDct["public_file"]

    bPublishable = True
    #sPubFilePath = pubFile.absPath()

    dbnode = pubFile.loadDbNode(fromDb=False)
    if dbnode:
        pubFile.refresh(simple=True, dbNode=refreshDbNode)
    elif refreshDbNode:
        dbnode = pubFile.loadDbNode(fromCache=False)

    sNewVersPath = resultDct["abs_path"]
    if pubFile.exists():
        try:
            pubFile._assertPublishable(sNewVersPath, refresh=False)
        except EnvironmentError as e:
            bPublishable = False
            sErrMsg = toStr(e)
    elif dbnode:
        sErrMsg = """File declared in database but does not exist on your server.
Wait for the next synchro and retry publishing."""
        bPublishable = False

    if not bPublishable:
        scanLogDct.setdefault("error", []).append(("NotPublishable", sErrMsg))
    else:
        bModified = True
        if pubFile.isFile():
            #bModified = (not filecmp.cmp(sNewVersPath, sPubFilePath))
            bModified, sChecksum = pubFile.differsFrom(sNewVersPath)
            resultDct["checksum"] = sChecksum

        if not bModified:
            scanLogDct.setdefault("info", []).append(("NotModified", "File has not been modified"))
        else:
            sMsg = "to {}\n".format(pubFile.absDirPath())
            sFellowFileList = resultDct["fellow_paths"]
            if sFellowFileList:
                sExtList = tuple(osp.basename(p).split(pubFile.baseName, 1)[-1]
                                 for p in sFellowFileList)
                sMsg = (", ".join(s.upper() for s in sExtList) + " found"
                        if sFellowFileList else "")
#            elif inDevMode():
#                sMsg = resultDct["abs_path"]

            scanLogDct.setdefault("info", []).append(("ReadyToPublish", sMsg))

    resultDct["publishable"] = bPublishable

    return bPublishable

def scanAllDependencyTypes(scnInfos, exclude=None):

    proj = scnInfos["project"]
    sSection = scnInfos["section"]
    sRcName = scnInfos["resource"]

    sExcDepList = argToTuple(exclude)

    depScanDct = {}
    for sDepType in proj.getDependencyTypes(sSection, sRcName).iterkeys():
        scanResults = None
        
        if sExcDepList and sDepType in sExcDepList:
            continue
        
        if sDepType == "texture_dep":
            scanResults = scanTextureFiles(scnInfos)
        elif sDepType == "geoCache_dep":
            scanResults = scanGeoCacheFiles(scnInfos)
        elif sDepType == "fxCache_dep":
            scanResults = scanFxCacheFiles(scnInfos)
        else:
            pm.displayWarning("Dependency type NOT supported yet: '{}'"
                              .format(sDepType))
        if scanResults:
            depScanDct[sDepType] = scanResults

    return depScanDct

dialog = None

def launch(scnInfos=None, scanFunc=None, modal=False, okLabel="OK",
           expandTree=False, forceDialog=False, exclude=None):

    global dialog

    if not scnInfos:
        scnInfos = infosFromScene()

    damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]

    if scanFunc is None:
        scanFunc = functools.partial(scanAllDependencyTypes, exclude=exclude)

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

