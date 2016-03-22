
#import os
import os.path as osp
import filecmp
#from datetime import datetime

import maya.cmds as mc
import maya.utils as mu
import pymel.core as pm

from . import dependency_scan
from davos_maya.tool.general import entityFromScene

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
def scanTexturesToEdit(damEntity):

    preEditResults = []
    sAllSeveritySet = set()

    def addResult(res):
#        for k, v in res.iteritems(): print k, v
#        print ""
        preEditResults.append(res)
        sAllSeveritySet.update(res["scan_log"].iterkeys())

    pubLib = damEntity.getLibrary()
    pubTexDir = damEntity.getResource("public", "texture_dir", fail=True)
    sPubTexDirPath = pubTexDir.absPath()
    pubTexDir.loadChildDbNodes()

    fileNodeList = fileNodesFromSelection()
    if not fileNodeList:
        return

    sSelTexPathSet = set(pathResolve(n.getAttr("fileTextureName"))
                         for n in fileNodeList)

    scanResults = dependency_scan.scanTextureFiles(damEntity)

    sPrivTexDirPath = damEntity.getPath("private", "texture_dir")
    bPrivTexDirFound = osp.exists(sPrivTexDirPath)

#    sDate = datetime.now().strftime("%Y-%m-%d_%HH%M")
#    sBkupTexDirName = "texture_edit_backup"

    sSelUdimFileSet = set()
    for srcRes in scanResults:
        if srcRes["abs_path"] in sSelTexPathSet:
            l = srcRes["udim_paths"]
            if l:
                sSelUdimFileSet.update(l)
                #print srcRes["abs_path"], srcRes["buddy_paths"]

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

        sPubPathList = [sPubTexPath] + srcRes["buddy_paths"]
        for i, sPubFilePath in enumerate(sPubPathList):

            scanLogDct = {}
            pubFile = pubLib.getEntry(sPubFilePath, dbNode=False)

            cachedDbNode = pubFile.getDbNode(fromDb=False)
            if cachedDbNode:
                pubFile.refresh(simple=True)
            else:
                pubFile.getDbNode(fromCache=False)

            if i == 0:
                resultDct = srcRes.copy()
                resultDct["scan_log"] = scanLogDct
            else:
                resultDct = {"abs_path":sPubFilePath,
                             "scan_log":scanLogDct,
                             "file_nodes":[],
                             "buddy_paths":[],
                             "publishable":False,
                             "drc_file":None,
                             }

            resultDct["public_file"] = pubFile

            if not pubFile.isUpToDate(refresh=False):
                sMsg = """The file appears to have been modified from another site.
File needs to be synced before you can edit it."""
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

            if "error" not in scanLogDct:
                scanLogDct.setdefault("info", []).append(('ReadyToEdit', ""))

            addResult(resultDct)

    if preEditResults:
        preEditResults[-1]["scan_severities"] = sAllSeveritySet
        preEditResults[-1]["publish_count"] = 0

    return preEditResults

def editTextureFiles(dryRun=False):

    sCurScnPath = pm.sceneName()
    damEntity = entityFromScene(sCurScnPath)

    proj = damEntity.project
    privLib = damEntity.getLibrary("private")

    privScnFile = privLib.getEntry(sCurScnPath)
    pubScnFile = privScnFile.getPublicFile(fail=True)

    pubScnFile.assertEditedVersion(privScnFile, outcomes=False, remember=False)
    pubScnFile.ensureLocked()

    preEditResults = dependency_scan.launch(damEntity, scanFunc=scanTexturesToEdit,
                                            modal=True,
                                            okLabel="Edit",
                                            expandTree=True,
                                            forceDialog=True)
    if preEditResults is None:
        pm.displayInfo("Canceled !")
        return

    pubFileItems = tuple((r["public_file"], r["file_nodes"]) for r in preEditResults
                         if "error" not in r["scan_log"])
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
    for pubFile, fileNodes in pubFileItems:

        privFile, bCopied = pubFile.copyToPrivateSpace(dry_run=dryRun)
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
