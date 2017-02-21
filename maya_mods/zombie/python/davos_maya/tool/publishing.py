
import os
import re
import glob
import subprocess
from tempfile import NamedTemporaryFile
from itertools import izip

import pymel.core as pm
import pymel.util as pmu
#import maya.cmds as mc

#from pytd.util.logutils import logMsg
from pytd.util.sysutils import toStr, inDevMode, timer
from pytd.gui.dialogs import confirmDialog
from pytd.util.fsutils import pathNormAll, pathResolve, pathNorm, pathJoin
from pytd.util.strutils import labelify
from pytaya.core import system as myasys
from pytaya.core import cleaning

from davos.core.damtypes import DamAsset
from davos.tools import publish_dependencies
from davos_maya.tool.general import infosFromScene, projectFromScene
from davos_maya.tool.general import listRelatedAssets
from davos_maya.tool import dependency_scan
from davos.core.drctypes import DrcPack
from pytd.util.logutils import logMsg

osp = os.path
FILE_PATH_ATTRS = dependency_scan.FILE_PATH_ATTRS

_DRY_RUN = False

class PublishContext(object):

    def __init__(self, scnInfos, prePublishInfos, **kwargs):
        self.prePublishInfos = prePublishInfos
        self.postPublishInfos = None
        self.sceneInfos = scnInfos

def publishSceneDependencies(scnInfos, sDependType, depScanResults, prePublishInfos, **kwargs):

    bDryRun = kwargs.pop("dryRun", False if not inDevMode() else _DRY_RUN)
    sComment = prePublishInfos["comment"]

    damEntity = scnInfos.get("dam_entity")
    sRcName = scnInfos.get("resource", "")
    sAbsScnPath = scnInfos.get("abs_path")
    if sAbsScnPath:
        sScnName = osp.basename(sAbsScnPath)
        if damEntity and sScnName.startswith(damEntity.name):
            sScnName = sScnName.split(damEntity.name, 1)[-1].strip("_")
        sComment = "published with '{}':\n{}".format(sScnName, toStr(sComment))

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
        dependDataDct[pathNormAll(sAbsPath)] = result

        if not result["publishable"]:
            continue

        if result["file_nodes"] or result.get("udim_paths"):
            sDependPathList.append(sAbsPath)
        else:
            sFellowPathList.append(sAbsPath)

        sAllSrcPathList.append(sAbsPath)

    if not sAllSrcPathList:
        pm.displayInfo("No dependencies to publish.")
        return

    if sDependPathList:

        if (not pm.about(batch=True)):
            pm.mel.ScriptEditor()
            pm.mel.handleScriptEditorAction("maximizeHistory")

        sDependLabel = labelify(sDependType.rsplit("_dep", 1)[0])
        print "\n" + " Publishing {} files ".format(sDependLabel).center(120, '-')

        publishedDependItems = publishDependencies(depConfDct,
                                                   sDependPathList,
                                                   dependDataDct,
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
                                                       dependDataDct,
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

    repathDependenciesToPublic(proj, depConfDct, sDependPathList,
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


def publishDependencies(depConfDct, sDepPathList, dependDataDct, sComment, **kwargs):

    bDryRun = kwargs.get("dryRun", False)

    bChecksum = depConfDct.get("checksum", False)
    depDir = depConfDct["dep_public_loc"]

    if isinstance(sDepPathList, list):
        publishItems = sDepPathList[:]
    else:
        publishItems = list(sDepPathList)

    if (not bDryRun) and (not depDir.exists()):
        os.makedirs(depDir.absPath())

    numDep = len(sDepPathList)
    for i, sDepPath in enumerate(sDepPathList):

        print u"Publishing {}/{}: '{}'".format(i + 1, numDep, sDepPath)

        depData = dependDataDct[pathNormAll(sDepPath)]
        sChecksum = depData.get("checksum", "")

        pubFile, versionFile = depDir.publishFile(sDepPath, autoLock=True,
                                                  autoUnlock=True,
                                                  saveChecksum=bChecksum,
                                                  checksum=sChecksum,
                                                  comment=sComment,
                                                  **kwargs)
        publishItems[i] = (pubFile, versionFile)

    depDir.refresh(children=True)

    return publishItems

def repathDependenciesToPublic(proj, depConfDct, sDepPathList, publishedItems,
                               dependDataDct, **kwargs):

    bDryRun = kwargs.pop("dryRun", False if not inDevMode() else _DRY_RUN)

    publishedItemsDct = dict(izip((pathNormAll(p) for p in sDepPathList),
                                  publishedItems))

    sMsgFmt = "\nRelinking '{}' node: \n    from '{}'\n      to '{}'"

    sEnvVarName = depConfDct.get("env_var", "")

    sLinkedList = []
    for sTexPath, pubItems in izip(sDepPathList, publishedItems):

        sTexNormPath = pathNormAll(sTexPath)

        pubFile = None
        depData = dependDataDct[sTexNormPath]

        sUdimPathList = depData.get("udim_paths")
        if sUdimPathList:
            sUdimPath = sUdimPathList[0]
            sUdimNormPath = pathNormAll(sUdimPath)
            if sUdimNormPath != sTexNormPath:
                pubFile = publishedItemsDct.get(sUdimNormPath, (None, None))[0]
                if not pubFile:
                    pubFile = proj.entryFromPath(sUdimPath, dbNode=False)
                depData = dependDataDct[sUdimNormPath]

        if pubFile is None:
            pubFile = pubItems[0]

        sPubEnvPath = pubFile.envPath(sEnvVarName)
        bIsPack = isinstance(pubFile, DrcPack)
        sPackSep = "/{}(/|$)".format(pubFile.name)

        fileNodeList = depData["file_nodes"]
        for fileNode in fileNodeList:

            sNodeName = fileNode.name()
            if sNodeName in sLinkedList:
                continue

            fileAttr = fileNode.attr(FILE_PATH_ATTRS[fileNode.type()])

            sSrcFilePath = pathNorm(pathResolve(fileAttr.get()))
            if bIsPack:
                #print fileNode, sSrcFilePath, sPackSep
                sEndPath = re.split(sPackSep, sSrcFilePath)[-1]
                sPubFilePath = pathJoin(sPubEnvPath, sEndPath)
            else:
                sPubFilePath = sPubEnvPath

            sMsg = (sMsgFmt.format(sNodeName, sSrcFilePath, sPubFilePath))
            print sMsg

            if not bDryRun:
                fileAttr.set(sPubFilePath)

            sLinkedList.append(sNodeName)


def lockSceneDependenciesToCurrentVersion(dryRun=False):

    scnInfos = infosFromScene()

    allDepScanResults = dependency_scan.scanAllDependencyTypes(scnInfos)
    for depScanResults in allDepScanResults.itervalues():
        lockDependenciesToCurrentVersion(scnInfos["project"], depScanResults, dryRun=dryRun)

def lockDependenciesToCurrentVersion(proj, depScanResults, **kwargs):

    bDryRun = kwargs.pop("dryRun", False)

    depDataList = []
    headFileList = []
    for depData in depScanResults:

        rcFile = depData["drc_file"]
        if not rcFile:
            continue

        if (not rcFile.isPublic()) or rcFile.isVersionFile():
            continue

        if not depData["file_nodes"]:
            continue

        depDataList.append(depData)
        headFileList.append(rcFile)

    proj.dbNodesFromEntries(headFileList)

    sMsgFmt = "\nRelinking '{}' node: \n    from '{}'\n      to '{}'"

    sLinkedList = []
    sNotFoundList = []
    for depData in depDataList:

        headFile = depData["drc_file"]

        try:
            versFile = headFile.assertLatestFile(refresh=False, returnVersion=True)
        except EnvironmentError as e:
            logMsg(e.message, warning=True)
            continue

        depData["version_file"] = versFile

        if not versFile:
            continue

        sHeadPath = "/" + headFile.relPath()
        sVersPath = "/" + versFile.relPath()

        fileNodeList = depData["file_nodes"]
        for fileNode in fileNodeList:

            sNodeName = fileNode.name()
            if sNodeName in sLinkedList:
                continue

            fileAttr = fileNode.attr(FILE_PATH_ATTRS[fileNode.type()])
            sCurPath = pathNorm(fileAttr.get())
            sNewPath = pathNorm(sCurPath.replace(sHeadPath, sVersPath))

            bExists = False
            sAbsPath = pathResolve(sNewPath)
            if "#" in osp.basename(sAbsPath):
                if glob.glob(sAbsPath.replace("#", "?")):
                    bExists = True
            else:
                bExists = osp.exists(sAbsPath)

            if bExists:
                sMsg = (sMsgFmt.format(sNodeName, sCurPath, sNewPath))
                print sMsg
                #print "\n".join((sCurPath, sHeadPath, sVersPath))
                if not bDryRun:
                    fileAttr.set(sNewPath)
            else:
                sNotFoundList.append((sNodeName, sAbsPath))

            sLinkedList.append(sNodeName)

    if sNotFoundList:
        sMsg = "No such files or directories:"
        for sNodeName, sAbsPath in sNotFoundList:
            sMsg += "\n   - {}: '{}'".format(sNodeName, sAbsPath)
    
        raise EnvironmentError(sMsg)

    return depDataList

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
    bDryRun = kwargs.pop("dryRun", False if not inDevMode() else _DRY_RUN)

    sCurScnPath = pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    myasys.assertCurrentSceneReadWithoutDataLoss()

    if not scnInfos:
        scnInfos = infosFromScene(sCurScnPath)

    damEntity = scnInfos.get("dam_entity")
    proj = scnInfos["project"]

    res = proj.assertEditedVersion(sCurScnPath)
    pubScnFile = res["public_file"]
    pubScnFile.ensureLocked(autoLock=False)
    scnInfos["public_file"] = pubScnFile

    try:
        quickSceneCleanUp(damEntity)
    except Exception as e:
        sConfirm = confirmDialog(title='INFO !',
                                 message="Quick cleanup failed !\n\n{0}".format(toStr(e)),
                                 button=['Continue', 'Abort'],
                                 defaultButton='Continue',
                                 cancelButton='Abort',
                                 dismissString='Continue',
                                 icon="information")
        if sConfirm == 'Abort':
            raise

    depScanDct = {}
    if damEntity and bWithDeps:

        sExcDepList = None

        sScnRcName = scnInfos.get("resource")
        if sScnRcName == "fx3d_scene":
            sRes = confirmDialog(title='DO YOU WANT TO...',
                                 message="Publish FX caches and textures ?",
                                 button=["Yes", "No"],
                                 dismissString="No",
                                 icon="question")

            if sRes == "No":
                sExcDepList = ["texture_dep", "fxCache_dep"]

        depScanDct = dependency_scan.launch(scnInfos, modal=True, okLabel="Publish",
                                            exclude=sExcDepList)
        if depScanDct is None:
            pm.displayInfo("Canceled !")
            return

    bSgVersion = True
    try:
        prePublishInfos = pubScnFile.beginPublish(sCurScnPath, checkLock=False, **kwargs)
        if prePublishInfos is None:
            return
        sgVersionData = prePublishInfos["sg_version_data"]
        publishCtx = PublishContext(scnInfos, prePublishInfos)
    except Exception, e:
        pubScnFile._abortPublish(e, None, None)
        raise

#    sgTask = sgVersionData["sg_task"]
    if not sgVersionData.get("sg_task"):
        bSgVersion = False

    if prePublishFunc:
        prePublishFunc(publishCtx)

    if damEntity and depScanDct:
        for sDepType, scanResults in depScanDct.iteritems():
            publishSceneDependencies(scnInfos, sDepType, scanResults, prePublishInfos, dryRun=bDryRun)
        if bDryRun:
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
                                    returnDict=True,
                                    **kwargs)

    publishCtx.postPublishInfos = res

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

def linkAssetVersionsInShotgun(damShot, sgVersion, relatedAssets=None, dryRun=False):

    def iterVersionEnvPaths(relAstList):
        for relAstData in relAstList:
            versFile = relAstData.get("version_file")
            if versFile:
                yield versFile.envPath()

#    sgShot = sgVersion["entity"]
    proj = damShot.project

    relatedAssetList = listRelatedAssets(damShot) if relatedAssets is None else relatedAssets
    if not relatedAssetList:
        return

    sVersPathList = tuple(iterVersionEnvPaths(relatedAssetList))
    sgVersList = []
    sgVersDct = {}
    if sVersPathList:
        filters = [["sg_source_file", "in", sVersPathList]]
        sgVersList = proj.findSgVersions(moreFilters=filters)
        sgVersDct = dict((osp.normcase(d["sg_source_file"]), d) for d in sgVersList)

#    shotConnList = []
    lockedSgVersList = []
    for relAstData in relatedAssetList:

        rcFile = relAstData.get("rc_entry")
        if not rcFile:
            continue

        versFile = relAstData["version_file"]
        if not versFile:
            continue

        sgVers = None
        if rcFile == versFile:
            sgVers = sgVersDct.get(osp.normcase(rcFile.envPath()))
            if sgVers:
                lockedSgVersList.append(sgVers)

#        astShotConn = relAstData.get("sg_asset_shot_conn")
#        if astShotConn:
#            astShotConn["sg_locked_to_version"] = sgVers
#            shotConnList.append(astShotConn)

    if not dryRun:
        sgVersion = proj.updateSgEntity(sgVersion, sg_locked_asset_versions=lockedSgVersList,
                                        sg_related_asset_versions=sgVersList)
#        proj.updateSgEntity(sgShot, sg_locked_asset_versions=lockedSgVersList)
#        for astShotConn in shotConnList:
#            proj.updateSgEntity(astShotConn, sg_locked_to_version=astShotConn.get("sg_locked_to_version"))
    else:
        sgVersion.update(sg_locked_asset_versions=lockedSgVersList,
                         sg_related_asset_versions=sgVersList)
    return sgVersion




