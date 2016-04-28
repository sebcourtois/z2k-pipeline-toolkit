
import os
import subprocess
from tempfile import NamedTemporaryFile

from itertools import izip
from collections import OrderedDict

import pymel.core as pm
import pymel.util as pmu
#import maya.cmds as mc

#from pytd.util.logutils import logMsg
from pytaya.core import system as myasys

from davos.tools import publish_dependencies

from .general import entityFromScene, projectFromScene
from davos_maya.tool import dependency_scan
from pytd.util.sysutils import toStr, inDevMode, timer
from pytd.gui.dialogs import confirmDialog
from pytd.util.fsutils import normCase
from davos.core.damtypes import DamAsset
from pytaya.core import cleaning

osp = os.path

bDevDryRun = False

class PublishContext(object):

    def __init__(self, proj, prePublishInfos, **kwargs):
        self.project = proj
        self.prePublishInfos = prePublishInfos
        self.entity = kwargs.get("entity")

def publishSceneDependencies(damEntity, depScanResults, prePublishInfos, **kwargs):

    bDryRun = kwargs.pop("dryRun", False if not inDevMode() else bDevDryRun)
    sComment = prePublishInfos["comment"]

    proj = damEntity.project

    sAllPathList = []
    sBuddyPathList = []
    sTexPathList = []
    depDataDct = {}
    for result in depScanResults:

        sAbsPath = result["abs_path"]
        depDataDct[normCase(sAbsPath)] = result

        if not result["publishable"]:
            continue

        if result["file_nodes"] or result["udim_paths"]:
            sTexPathList.append(sAbsPath)
        else:
            sBuddyPathList.append(sAbsPath)

        sAllPathList.append(sAbsPath)

    if not sAllPathList:
        pm.displayInfo("No dependencies to publish.")
        return (not bDryRun)

    if sTexPathList:

        pm.mel.ScriptEditor()
        pm.mel.handleScriptEditorAction("maximizeHistory")

        print "\n" + " Publishing texture files ".center(120, '-')

        publishItemsList = proj.publishDependencies("texture_dep",
                                                      damEntity,
                                                      sTexPathList,
                                                      sComment,
                                                      dryRun=bDryRun,
                                                      **kwargs)

        publishItemsDct = OrderedDict(izip((normCase(p) for p in sTexPathList),
                                            publishItemsList))

        sMsgFmt = "\nRelinking '{}' node: \n    from '{}'\n      to '{}'"

        sUnchangedList = []
        sUpdNodeList = []
        for sTexPath, publishItems in izip(sTexPathList, publishItemsList):

            versionFile = publishItems[1]
            if not versionFile:
                sUnchangedList.append(sTexPath)

            sTexNormPath = normCase(sTexPath)

            pubFile = None
            depData = depDataDct[sTexNormPath]

            sUdimPathList = depData["udim_paths"]
            if sUdimPathList:
                sUdimPath = sUdimPathList[0]
                sUdimNormPath = normCase(sUdimPath)
                if sUdimNormPath != sTexNormPath:
                    pubFile = publishItemsDct.get(sUdimNormPath, (None, None))[0]
                    if not pubFile:
                        pubFile = proj.entryFromPath(sUdimPath, dbNode=False)
                    depData = depDataDct[sUdimNormPath]

            if pubFile is None:
                pubFile = publishItems[0]

            sPubEnvPath = pubFile.envPath("ZOMB_TEXTURE_PATH")

            fileNodeList = depData["file_nodes"]
            for fileNode in fileNodeList:

                sNodeName = fileNode.name()
                if sNodeName in sUpdNodeList:
                    continue

                sMsg = (sMsgFmt.format(sNodeName,
                                       fileNode.getAttr("fileTextureName"),
                                       sPubEnvPath))
                print sMsg

                if not bDryRun:
                    fileNode.setAttr("fileTextureName", sPubEnvPath)

                sUpdNodeList.append(sNodeName)

    if sBuddyPathList:
        bUseSubprocess = False
        if not bUseSubprocess:

            print "\n" + " Publishing related files (.psd, .tx, etc...) ".center(120, '-')

            publishItemsList = proj.publishDependencies("texture_dep",
                                                         damEntity,
                                                         sBuddyPathList,
                                                         sComment,
                                                         dryRun=bDryRun,
                                                         **kwargs)

            for sBuddyPath, publishItems in izip(sBuddyPathList, publishItemsList):
                versionFile = publishItems[1]
                if not versionFile:
                    sUnchangedList.append(sBuddyPath)

        else:
            sMsg = """
    Opening a new process to publish associated files: .psd, .tx, etc...
        """
            pm.displayWarning(sMsg)

            with NamedTemporaryFile(suffix=".txt", delete=False) as tmpFile:
                tmpFile.write("\n".join(sBuddyPathList))

            p = publish_dependencies.__file__

            sPython27Path = r"C:\Python27\python.exe"
            sScriptPath = p[:-1]if p.endswith("c") else p
            sCmdArgs = [sPython27Path,
                        os.environ["Z2K_LAUNCH_SCRIPT"],
                        "launch", "--update", "0", "--renew", "1",
                        sPython27Path,
                        sScriptPath,
                        proj.name, "texture_dep",
                        damEntity.sgEntityType.lower(),
                        damEntity.name, tmpFile.name,
                        sComment, "--dryRun", str(int(bDryRun)),
                        ]

            sCmdArgs = list(toStr(a)for a in sCmdArgs)
            if inDevMode():
                print sCmdArgs

            subprocess.Popen(sCmdArgs)

    total = len(sAllPathList)
    sSep = "\n"

    w = len(max(sAllPathList, key=len))

    sUpdatedList = sAllPathList
    if sUnchangedList:
        count = len(sUnchangedList)
        sMsgTag = " Unchanged files: {}/{} ".format(count, total).center(w, '-')
        sMsgFiles = sSep.join(sUnchangedList)
        print sSep + sSep.join((sMsgTag, sMsgFiles, sMsgTag))

        sUpdatedList = list(p for p in sAllPathList if p not in sUnchangedList)

    if sUpdatedList:
        count = len(sUpdatedList)
        sMsgTag = " Updated files: {}/{} ".format(count, total).center(w, '-')
        sMsgFiles = sSep.join(sUpdatedList)
        print sSep + sSep.join((sMsgTag, sMsgFiles, sMsgTag))

    return (not bDryRun)

def quickSceneCleanUp(damEntity):

    from dminutes import miscUtils
    pm.mel.source("cleanUpScene.mel")

    if isinstance(damEntity, DamAsset):

        miscUtils.deleteUnknownNodes()

        cleaning.unsmoothAllMeshes()
        cleaning.cleanLambert1()

    # optimize scene
    pmu.putEnv("MAYA_TESTING_CLEANUP", "1")
    sCleanOptions = ("referencedOption",)
    pm.mel.scOpt_performOneCleanup(sCleanOptions)
    pmu.putEnv("MAYA_TESTING_CLEANUP", "")

def publishCurrentScene(*args, **kwargs):

    bWithDeps = kwargs.pop("dependencies", True)
    prePublishFunc = kwargs.pop("prePublishFunc", None)
    postPublishFunc = kwargs.pop("postPublishFunc", None)
    damEntity = kwargs.pop("entity", None)

    myasys.assertCurrentSceneReadWithoutDataLoss()

    sCurScnPath = pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    if not damEntity:
        damEntity = entityFromScene(sCurScnPath, fail=False)

    if damEntity:
        proj = damEntity.project
    else:
        proj = projectFromScene(sCurScnPath)

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

    depScanResults = []
    if damEntity and bWithDeps:
        depScanResults = dependency_scan.launch(damEntity, modal=True, okLabel="Publish")
        if depScanResults is None:
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

    if damEntity and depScanResults:
        if not publishSceneDependencies(damEntity, depScanResults, prePublishInfos):
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
