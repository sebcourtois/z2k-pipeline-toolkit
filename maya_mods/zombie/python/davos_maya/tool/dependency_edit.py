
#import os
import os.path as osp
import filecmp
#from datetime import datetime

import maya.cmds as mc
import maya.utils as mu
import pymel.core as pm

from . import dependency_scan
from davos_maya.tool.general import infosFromScene

from pytaya.core.rendering import fileNodesFromObjects, fileNodesFromShaders
from pytd.util.fsutils import pathResolve, normCase
from pytd.util.qtutils import setWaitCursor

#from pytd.util.sysutils import toStr


def fileNodesFromSelection():

    sSelList = mc.ls(sl=True)

    oFileNodeList = []
    sConfirmMsg = ""

    if not sSelList:
        oFileNodeList = pm.ls("*", r=True, type="file")
        sConfirmMsg = "Edit All Texture Files ??"
    else:
        oFileNodeList = pm.ls(sSelList, type='file')
        oFileNodeList.extend(fileNodesFromShaders(pm.ls(sSelList, type=mc.listNodeTypes('shader', ex="texture"))))
        oFileNodeList.extend(fileNodesFromObjects(pm.ls(sSelList, dag=True, shapes=True)))

        #sFiles = '\n'.join("'{}'".format(osp.basename(n.getAttr('fileTextureName'))) for n in oFileNodeList)
        #sConfirmMsg = "Edit {} selected textures:\n\n".format(len(oFileNodeList))
        #sConfirmMsg += sFiles

    if not oFileNodeList:
        pm.warning("No File node found in current selection !")
        return

    if sConfirmMsg:
        sConfirm = pm.confirmDialog(title='QUESTION !',
                                    message=sConfirmMsg,
                                    button=['OK', 'Cancel'])

        if sConfirm == 'Cancel':
            pm.warning("Canceled !")
            return

    return oFileNodeList

@setWaitCursor
def scanTexturesToEdit(scnInfos):

    preEditResults = []
    sAllSeveritySet = set()

    def addResult(res):
#        for k, v in res.iteritems(): print k, v
#        print ""
        preEditResults.append(res)
        sAllSeveritySet.update(res["scan_log"].iterkeys())

    damEntity = scnInfos.get("dam_entity")
    #proj = scnInfos["project"]
    pubLib = damEntity.getLibrary()

    sDepType = "texture_dep"
    depConfDct = damEntity.getDependencyConf(sDepType, scnInfos["resource"])
    pubDepDir = depConfDct["dep_public_loc"]
    sPrivTexDirPath = depConfDct["dep_source_loc"]
    bPrivTexDirFound = osp.exists(sPrivTexDirPath)

    fileNodeList = fileNodesFromSelection()
    if not fileNodeList:
        return

    sPubTexDirPath = pubDepDir.absPath()
    if pubDepDir.exists():
        pubDepDir.loadChildDbNodes()

    sSelTexPathSet = set(pathResolve(n.getAttr("fileTextureName"))
                         for n in fileNodeList)

    scanResults = dependency_scan.scanTextureFiles(scnInfos, depConfDct)

#    sDate = datetime.now().strftime("%Y-%m-%d_%HH%M")
#    sBkupTexDirName = "texture_edit_backup"

    sSelUdimFileSet = set()
    for srcRes in scanResults:
        if srcRes["abs_path"] in sSelTexPathSet:
            l = srcRes["udim_paths"]
            if l:
                sSelUdimFileSet.update(l)
                #print srcRes["abs_path"], srcRes["fellow_paths"]

    for srcRes in scanResults:

        infos = srcRes["scan_log"].get("info")
        if not infos:
            continue

        texFile = srcRes["drc_file"]
        if not texFile:
            continue

        if texFile.isPrivate():
            continue

        sPubTexPath = texFile.absPath()
        sTexDirPath = osp.dirname(sPubTexPath)
        if normCase(sTexDirPath) != normCase(sPubTexDirPath):
            continue

        if sPubTexPath not in sSelTexPathSet:
            if sPubTexPath not in sSelUdimFileSet:
                continue

        sPubPathList = [sPubTexPath] + srcRes["fellow_paths"]
        for i, sPubFilePath in enumerate(sPubPathList):

            scanLogDct = {}
            pubFile = pubLib.getEntry(sPubFilePath, dbNode=False)

            cachedDbNode = pubFile.loadDbNode(fromDb=False)
            if cachedDbNode:
                pubFile.refresh(simple=True)
            else:
                pubFile.loadDbNode(fromCache=False)

            if i == 0:
                resultDct = srcRes.copy()
                resultDct["scan_log"] = scanLogDct
            else:
                resultDct = {"dependency_type":"texture_dep",
                             "abs_path":sPubFilePath,
                             "scan_log":scanLogDct,
                             "file_nodes":[],
                             "fellow_paths":[],
                             "publishable":False,
                             "drc_file":None,
                             "latest_file":None,
                             }

            resultDct["public_file"] = pubFile

            try:
                editSrcFile = pubFile.assertLatestFile(refresh=False)
            except EnvironmentError as e:
                scanLogDct.setdefault("error", []).append(('FileOutOfSync', e.message))
            else:
                sEditSrcPath = sPubFilePath
                if editSrcFile != pubFile:
                    resultDct["latest_file"] = editSrcFile
                    sEditSrcPath = editSrcFile.absPath()

                privFile = pubFile.getPrivateFile(weak=True)
                if (bPrivTexDirFound and privFile.exists()):

                    sPrivFilePath = privFile.absPath()
                    #bDiffers, _ = pubFile.differsFrom(sPrivFilePath)
                    bDiffers = (not filecmp.cmp(sPrivFilePath, sEditSrcPath))
                    #print '\n', '\n'.join((str(bDiffers), sPrivFilePath, sEditSrcPath))
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

            if "error" not in scanLogDct:
                scanLogDct.setdefault("info", []).append(('ReadyToEdit', ""))

            addResult(resultDct)

    if preEditResults:
        preEditResults[-1]["scan_severities"] = sAllSeveritySet
        preEditResults[-1]["publish_count"] = 0

    return {"texture_dep":preEditResults}

def editTextureFiles(dryRun=False):

    sCurScnPath = pm.sceneName()
    scnInfos = infosFromScene(sCurScnPath)

    #damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]

    privScnFile = scnInfos["rc_entry"]
    pubScnFile = privScnFile.getPublicFile(fail=True)

    pubScnFile.assertEditedVersion(privScnFile, outcomes=False, remember=False)
    pubScnFile.ensureLocked()

    preEditScanDct = dependency_scan.launch(scnInfos, scanFunc=scanTexturesToEdit,
                                            modal=True,
                                            okLabel="Edit",
                                            expandTree=True,
                                            forceDialog=True)
    if preEditScanDct is None:
        pm.displayInfo("Canceled !")
        return

    preEditResults = preEditScanDct["texture_dep"]

    pubFileItems = tuple((d["public_file"], d.get("latest_file"), d["file_nodes"])
                            for d in preEditResults
                                if "error" not in d["scan_log"])
    if not pubFileItems:
        pm.displayWarning("No public textures to edit !")
        return

    def showScriptEditor():
        pm.mel.ScriptEditor()
        pm.mel.handleScriptEditorAction("maximizeHistory")
    mu.executeInMainThreadWithResult(showScriptEditor)

    sMsgFmt = "\nRelinking '{}' node: \n    from '{}'\n      to '{}'"
    privFile = None
    sCopiedList = []
    numLinked = 0
    for pubFile, latestFile, fileNodes in pubFileItems:

        privFile, bCopied = pubFile.copyToPrivateSpace(dry_run=dryRun,
                                                       sourceFile=latestFile)
        if bCopied:
            sCopiedList.append(privFile.name)
        sPrivAbsPath = privFile.absPath()

        for fileNode in fileNodes:

            sCurNodePath = fileNode.getAttr("fileTextureName")
            curNodeFile = proj.entryFromPath(pathResolve(sCurNodePath), dbNode=False)
            if curNodeFile.isPublic():
                sMsg = sMsgFmt.format(fileNode.name(), sCurNodePath, sPrivAbsPath)
                print sMsg
                if not dryRun:
                    fileNode.setAttr("fileTextureName", sPrivAbsPath)
                numLinked += 1

    if sCopiedList:
        privFile.showInExplorer()

    pm.displayInfo("copied files: {} -  relinked textures: {}."
                   .format(len(sCopiedList), numLinked))
