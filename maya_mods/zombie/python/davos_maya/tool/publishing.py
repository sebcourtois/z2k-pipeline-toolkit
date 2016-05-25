
import os
import subprocess
from tempfile import NamedTemporaryFile
from itertools import izip

import pymel.core as pm
import pymel.util as pmu
#import maya.cmds as mc

#from pytd.util.logutils import logMsg
from pytaya.core import system as myasys

from davos.tools import publish_dependencies

from .general import infosFromScene, projectFromScene
from davos_maya.tool import dependency_scan
from pytd.util.sysutils import toStr, inDevMode, timer
from pytd.gui.dialogs import confirmDialog
from pytd.util.fsutils import normCase
from davos.core.damtypes import DamAsset
from pytaya.core import cleaning
from pytd.util.strutils import labelify

osp = os.path

bDevDryRun = False

class PublishContext(object):

    def __init__(self, proj, prePublishInfos, **kwargs):
        self.project = proj
        self.prePublishInfos = prePublishInfos
        self.entity = kwargs.get("entity")

def publishSceneDependencies(scnInfos, sDependType, depScanResults, prePublishInfos, **kwargs):

    bDryRun = kwargs.pop("dryRun", False if not inDevMode() else bDevDryRun)
    sComment = prePublishInfos["comment"]

    damEntity = scnInfos["dam_entity"]
    sRcName = scnInfos.get("resource", "")

    depConfDct = damEntity.getDependencyConf(sDependType, sRcName)

    proj = damEntity.project

    sAllSrcPathList = []
    sFellowPathList = []
    sDependPathList = []
    dependDataDct = {}
    for result in depScanResults:

        if result["dependency_type"] != sDependType:
            continue

        sAbsPath = result["abs_path"]
        dependDataDct[normCase(sAbsPath)] = result

        if not result["publishable"]:
            continue

        if result["file_nodes"] or result.get("udim_paths"):
            sDependPathList.append(sAbsPath)
        else:
            sFellowPathList.append(sAbsPath)

        sAllSrcPathList.append(sAbsPath)

    if not sAllSrcPathList:
        pm.displayInfo("No dependencies to publish.")
        return (not bDryRun)

    if sDependPathList:

        pm.mel.ScriptEditor()
        pm.mel.handleScriptEditorAction("maximizeHistory")

        sDependLabel = labelify(sDependType.rsplit("_dep", 1)[0])
        print "\n" + " Publishing {} files ".format(sDependLabel).center(120, '-')

        publishedDependItems = publishDependencies(depConfDct,
                                                   sDependPathList,
                                                   sComment,
                                                   dryRun=bDryRun,
                                                   **kwargs)

        sUnchangedList = list(_filterNotPublishedPaths(sDependPathList, publishedDependItems))

    if sFellowPathList:
        bUseSubprocess = False
        if not bUseSubprocess:

            print "\n" + " Publishing fellow files (.psd, .tx, etc...) ".center(120, '-')

            publishedFellowItems = publishDependencies(depConfDct,
                                                       sFellowPathList,
                                                       sComment,
                                                       dryRun=bDryRun,
                                                       **kwargs)

            sUnchangedList.extend(_filterNotPublishedPaths(sFellowPathList, publishedFellowItems))

        else:
            sMsg = """
    Opening a new process to publish fellow files: .psd, .tx, etc...
        """
            pm.displayWarning(sMsg)

            with NamedTemporaryFile(suffix=".txt", delete=False) as tmpFile:
                tmpFile.write("\n".join(sFellowPathList))

            p = publish_dependencies.__file__

            sPython27Path = r"C:\Python27\python.exe"
            sScriptPath = p[:-1]if p.endswith("c") else p
            sCmdArgs = [sPython27Path,
                        os.environ["Z2K_LAUNCH_SCRIPT"],
                        "launch", "--update", "0", "--renew", "1",
                        sPython27Path,
                        sScriptPath,
                        proj.name, sDependType,
                        damEntity.sgEntityType.lower(),
                        damEntity.name, tmpFile.name,
                        sComment, "--dryRun", str(int(bDryRun)),
                        ]

            sCmdArgs = list(toStr(a)for a in sCmdArgs)
            if inDevMode():
                print sCmdArgs

            subprocess.Popen(sCmdArgs)

    linkDependenciesToPublic(proj, depConfDct, sDependPathList,
                             publishedDependItems, dependDataDct, dryRun=bDryRun)

    total = len(sAllSrcPathList)
    sSep = "\n"

    w = len(max(sAllSrcPathList, key=len))

    sUpdatedList = sAllSrcPathList
    if sUnchangedList:
        count = len(sUnchangedList)
        sMsgTag = " Unchanged files: {}/{} ".format(count, total).center(w, '-')
        sMsgFiles = sSep.join(sUnchangedList)
        print sSep + sSep.join((sMsgTag, sMsgFiles, sMsgTag))

        sUpdatedList = list(p for p in sAllSrcPathList if p not in sUnchangedList)

    if sUpdatedList:
        count = len(sUpdatedList)
        sMsgTag = " Published files: {}/{} ".format(count, total).center(w, '-')
        sMsgFiles = sSep.join(sUpdatedList)
        print sSep + sSep.join((sMsgTag, sMsgFiles, sMsgTag))

    return (not bDryRun)

def publishDependencies(depConfDct, sDepPathList, sComment, **kwargs):

    bDryRun = kwargs.get("dryRun", False)

    bChecksum = depConfDct.get("checksum", False)
    depDir = depConfDct["public_loc"]

    if isinstance(sDepPathList, list):
        publishItems = sDepPathList[:]
    else:
        publishItems = list(sDepPathList)

    if (not bDryRun) and (not depDir.exists()):
        os.makedirs(depDir.absPath())

    numDep = len(sDepPathList)
    for i, sDepPath in enumerate(sDepPathList):

        print u"Publishing file {}/{}: '{}'".format(i + 1, numDep, sDepPath)

        pubFile, versionFile = depDir.publishFile(sDepPath, autoLock=True,
                                                  autoUnlock=True,
                                                  saveChecksum=bChecksum,
                                                  comment=sComment,
                                                  **kwargs)
        publishItems[i] = (pubFile, versionFile)

    depDir.refresh(children=True)

    return publishItems

def linkDependenciesToPublic(proj, depConfDct, sDepPathList, publishedItems,
                             dependDataDct, **kwargs):

    bDryRun = kwargs.pop("dryRun", False if not inDevMode() else bDevDryRun)

    publishedItemsDct = dict(izip((normCase(p) for p in sDepPathList),
                                        publishedItems))

    sMsgFmt = "\nRelinking '{}' node: \n    from '{}'\n      to '{}'"

    sEnvVarName = depConfDct.get("env_var", "")

    sLinkedList = []
    for sTexPath, pubItems in izip(sDepPathList, publishedItems):

        sTexNormPath = normCase(sTexPath)

        pubFile = None
        depData = dependDataDct[sTexNormPath]

        sUdimPathList = depData.get("udim_paths")
        if sUdimPathList:
            sUdimPath = sUdimPathList[0]
            sUdimNormPath = normCase(sUdimPath)
            if sUdimNormPath != sTexNormPath:
                pubFile = publishedItemsDct.get(sUdimNormPath, (None, None))[0]
                if not pubFile:
                    pubFile = proj.entryFromPath(sUdimPath, dbNode=False)
                depData = dependDataDct[sUdimNormPath]

        if pubFile is None:
            pubFile = pubItems[0]

        sPubEnvPath = pubFile.envPath(sEnvVarName)

        fileNodeList = depData["file_nodes"]
        for fileNode in fileNodeList:

            sNodeName = fileNode.name()
            if sNodeName in sLinkedList:
                continue

            fileAttr = fileNode.listAttr(usedAsFilename=True)[0]

            sMsg = (sMsgFmt.format(sNodeName, fileAttr.get(), sPubEnvPath))
            print sMsg

            if not bDryRun:
                fileAttr.set(sPubEnvPath)

            sLinkedList.append(sNodeName)

def _filterNotPublishedPaths(sSrcPathList, publishedItems):
    for sSrcPath, pubItems in izip(sSrcPathList, publishedItems):
        versionFile = pubItems[1]
        if not versionFile:
            yield sSrcPath

def quickSceneCleanUp(damEntity):

    from dminutes import miscUtils
    pm.mel.source("cleanUpScene.mel")

    if isinstance(damEntity, DamAsset):

        miscUtils.deleteUnknownNodes()

        cleaning.unsmoothAllMeshes()
        cleaning.cleanLambert1()

    # optimize scene
    pmu.putEnv("MAYA_TESTING_CLEANUP", "1")
    sCleanOptList = ("referencedOption",)
    try:
        pm.mel.scOpt_performOneCleanup(sCleanOptList)
    finally:
        pmu.putEnv("MAYA_TESTING_CLEANUP", "")

def publishCurrentScene(*args, **kwargs):

    bWithDeps = kwargs.pop("dependencies", True)
    prePublishFunc = kwargs.pop("prePublishFunc", None)
    postPublishFunc = kwargs.pop("postPublishFunc", None)
    scnInfos = kwargs.pop("sceneInfos", None)

    sCurScnPath = pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    myasys.assertCurrentSceneReadWithoutDataLoss()

    if not scnInfos:
        scnInfos = infosFromScene(sCurScnPath)

    damEntity = scnInfos["dam_entity"]
    proj = scnInfos["project"]

    res = proj.assertEditedVersion(sCurScnPath)
    curPubFile = res["public_file"]
    curPubFile.ensureLocked(autoLock=False)

    try:
        quickSceneCleanUp(damEntity)
    except Exception as e:
        sConfirm = confirmDialog(title='INFO !',
                                 message="Quick cleanup failed !\n\n{0}".format(toStr(e)),
                                 button=['Continue', 'Cancel'],
                                 defaultButton='Continue',
                                 cancelButton='Cancel',
                                 dismissString='Continue',
                                 icon="information")
        if sConfirm == 'Cancel':
            raise

    depScanDct = {}
    if damEntity and bWithDeps:
        depScanDct = dependency_scan.launch(scnInfos, modal=True, okLabel="Publish")
        if depScanDct is None:
            pm.displayInfo("Canceled !")
            return

    bSgVersion = True
    try:
        prePublishInfos = curPubFile.beginPublish(sCurScnPath, checkLock=False, **kwargs)
        if prePublishInfos is None:
            return
        sgVersionData = prePublishInfos["sg_version_data"]
    except Exception, e:
        curPubFile._abortPublish(e, None, None)
        raise

#    sgTask = sgVersionData["sg_task"]
    if not sgVersionData.get("sg_task"):
        bSgVersion = False

    publishCtx = PublishContext(proj, prePublishInfos, entity=damEntity)

    if prePublishFunc:
        prePublishFunc(publishCtx)

    if damEntity and depScanDct:
        for sDepType, scanResults in depScanDct.iteritems():
            if not publishSceneDependencies(scnInfos, sDepType,
                                            scanResults, prePublishInfos):
                return

    sSavedScnPath = myasys.saveScene(prompt=False, checkError=False)
    if not sSavedScnPath:
        raise RuntimeError("Failed to save current scene !")

    res = proj.publishEditedVersion(sSavedScnPath,
                                    version=prePublishInfos["version"],
                                    comment=prePublishInfos["comment"],
                                    #sgTask=sgTask,
                                    withSgVersion=bSgVersion,
                                    sgVersionData=sgVersionData,
                                    **kwargs)

    if postPublishFunc:
        postPublishFunc(publishCtx)

    pm.displayWarning("Publishing completed !")

    return res

@timer
def linkSceneDependencies(sCurScnPath, depScanResults, sDependencyType):

    if not depScanResults:
        return

    proj = projectFromScene(sCurScnPath)

    scnFile = proj.entryFromPath(sCurScnPath, dbNode=False)
    if scnFile.isPrivate():
        scnFile = scnFile.getPublicFile(fail=True, dbNode=False)

    depFileList = []
    sAnyPathList = []

    for depData in depScanResults:

        if not depData["file_nodes"]:
            continue

        drcFile = depData["drc_file"]
        if drcFile:
            depFileList.append(drcFile)
        else:
            sAbsPath = depData["abs_path"]
            sAnyPathList.append(sAbsPath)

    data = {"link_type":"dependency", "dependency_type":sDependencyType}

    return proj.linkResourceFiles(scnFile, depFileList, data)
