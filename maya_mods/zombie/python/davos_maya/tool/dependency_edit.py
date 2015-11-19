
#import os
import os.path as osp
import filecmp
#from datetime import datetime

import maya.utils as mu
import pymel.core as pm

from . import dependency_scan
from davos_maya.tool.general import entityFromScene

from pytaya.core.rendering import fileNodesFromObjects
from pytd.util.fsutils import pathResolve

#from pytd.util.sysutils import toStr


def fileNodesFromSelection():

    oSelList = pm.selected(transforms=True, shapes=True)

    oFileNodeList = []

    if not oSelList:
        oFileNodeList = pm.ls("*", r=True, type="file")
        sConfirmMsg = "Edit All Texture Files ??"
    else:
        oFileNodeList = fileNodesFromObjects(pm.selected(dag=True, shapes=True))
        sConfirmMsg = "Edit {} Texture Files from selection ?".format(len(oFileNodeList))

    if not oFileNodeList:
        pm.warning("No Texture File found from current selection !")
        return

    sConfirm = pm.confirmDialog(title='QUESTION !'
                                , message=sConfirmMsg
                                , button=['OK', 'Cancel'])

    if sConfirm == 'Cancel':
        pm.warning("Canceled !")
        return

    return oFileNodeList


def editTextureFiles(dryRun=False):

    sCurScnPath = pm.sceneName()
    damEntity = entityFromScene(sCurScnPath)

    proj = damEntity.project
    privScnFile = proj.entryFromPath(sCurScnPath)
    pubScnFile = privScnFile.getPublicFile(fail=True)

    pubScnFile.assertEditedVersion(privScnFile)
    pubScnFile.ensureLocked()

    pubTexDir = damEntity.getResource("public", "texture_dir", fail=True)
    pubTexDir.loadChildDbNodes()

    fileNodeList = fileNodesFromSelection()
    if not fileNodeList:
        return

    sSelTexPathSet = set(pathResolve(n.getAttr("fileTextureName"))
                         for n in fileNodeList)

    scanResults = dependency_scan.scanTextureDependency(damEntity)

    sPrivTexDirPath = damEntity.getPath("private", "texture_dir")
    bPrivTexDirFound = osp.exists(sPrivTexDirPath)

#    sDate = datetime.now().strftime("%Y-%m-%d_%HH%M")
#    sBkupTexDirName = "texture_edit_backup"

    preEditResults = []
    sAllSeveritySet = set()

    def addResult(res):
#        for k, v in res.iteritems(): print k, v
#        print ""
        preEditResults.append(res)
        sAllSeveritySet.update(res["scan_log"].iterkeys())

    pubFileItems = []

    sSelUdimFileSet = set()
    for srcRes in scanResults:
        if srcRes["abs_path"] in sSelTexPathSet:
            l = srcRes["udim_files"]
            if l:
                sSelUdimFileSet.update(l)
                #print srcRes["abs_path"], srcRes["buddy_files"]

    for srcRes in scanResults:

        infos = srcRes["scan_log"].get("info")
        if not infos:
            continue

        if "PublicFiles" not in dict(infos):
            continue

        sPubTexPath = srcRes["abs_path"]
        if sPubTexPath not in sSelTexPathSet:
            if sPubTexPath not in sSelUdimFileSet:
                continue

        sPubPathList = [sPubTexPath] + srcRes["buddy_files"]
        for i, sPubFilePath in enumerate(sPubPathList):

            scanLogDct = {}
            pubFile = proj.entryFromPath(sPubFilePath)

            if not pubFile.isUpToDate():
                sMsg = "Sorry, you have to wait for the file to be synced"
                scanLogDct.setdefault("error", []).append(('FileOutOfSync', sMsg))
                #print "File is OUT OF SYNC: '{}'".format(sPubTexPath)
            else:
                privFile = pubFile.getPrivateFile(weak=True)
                if (bPrivTexDirFound and privFile.exists()):

                    sPrivFilePath = privFile.absPath()
                    #bDiffers, _ = pubFile.differsFrom(sPrivFilePath)
                    bDiffers = (not filecmp.cmp(sPrivFilePath, sPubFilePath))
                    #print '\n', '\n'.join((str(bDiffers), sPrivFilePath, sPubFilePath))
                    if bDiffers:
                        sMsg = "a DIFFERENT VERSION already EXISTS in your TEXTURE directory: "
                        sMsg += osp.normpath(sPrivTexDirPath)
                        sMsg += '\nDelete, move or rename this existing file and retry'
                        scanLogDct.setdefault("error", []).append(('PrivateFileFound', sMsg))
#                        try:
#                            os.rename(sPrivFilePath, sPrivFilePath)
#                        except OSError as e:
#                            sMsg = toStr(e)
#                            scanLogDct.setdefault("error", []).append(('FileInUse', sMsg))
            if i == 0:
                resultDct = srcRes.copy()
                resultDct["scan_log"] = scanLogDct
            else:
                resultDct = {"abs_path":sPubFilePath,
                             "scan_log":scanLogDct,
                             "file_nodes":[],
                             "buddy_files":[],
                             "publishable":False,
                             "drc_file":None,
                             }
            addResult(resultDct)

            if "error" not in scanLogDct:
                pubFileItems.append((pubFile, resultDct["file_nodes"]))

    if preEditResults:
        preEditResults[-1]["scan_severities"] = sAllSeveritySet
        preEditResults[-1]["publish_count"] = 0

    res = dependency_scan.launch(damEntity, scanResults=preEditResults, modal=True)
    if res is None:
        pm.displayInfo("Canceled !")
        return

    if not pubFileItems:
        pm.displayWarning("No public textures to edit in current scene !")
        return

    sMsgFmt = "\nUpdating {} path: \nfrom '{}'\n  to '{}'"

    privFile = None

    def showScriptEditor():
        pm.mel.ScriptEditor()
        pm.mel.handleScriptEditorAction("maximizeHistory")
    mu.executeInMainThreadWithResult(showScriptEditor)

    for pubFile, fileNodes in pubFileItems:

        privFile, _ = pubFile.copyToPrivateSpace(dry_run=dryRun)
        sAbsPath = privFile.absPath()

        for fileNode in fileNodes:

            sMsg = (sMsgFmt.format(repr(fileNode),
                                   fileNode.getAttr("fileTextureName"),
                                   sAbsPath))
            print sMsg

            if not dryRun:
                fileNode.setAttr("fileTextureName", sAbsPath)

    if privFile:
        privFile.showInExplorer()
        pm.displayInfo("{} public files copied and linked to your texture directory !"
                       .format(len(pubFileItems)))
