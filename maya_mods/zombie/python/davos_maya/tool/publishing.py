
import os
import subprocess
from tempfile import NamedTemporaryFile

from itertools import izip
from collections import OrderedDict

import pymel.core as pm

#from pytd.util.logutils import logMsg
from pytaya.core import system as myasys

#from pytd.gui.dialogs import confirmDialog
#from pytd.util.logutils import logMsg
#from pytaya.core.general import lsNodes
#from pytd.util.fsutils import pathResolve

from davos.tools import publish_dependencies

from .general import entityFromScene, projectFromScene
from davos_maya.tool import dependency_scan
from pytd.util.sysutils import toStr, inDevMode
from pytd.gui.dialogs import confirmDialog
from pytd.util.fsutils import normCase
#from pytd.util.fsutils import pathRelativeTo

bDevDryRun = False

def publishSceneDependencies(damEntity, scanResults, sComment, **kwargs):

    bDryRun = kwargs.pop("dryRun", False if not inDevMode() else bDevDryRun)

    proj = damEntity.project

    sAllPathList = []
    sBuddyPathList = []
    sTexPathList = []
    depDataDct = {}
    for result in scanResults:

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

def quickSceneCleanUp():

    from dminutes import miscUtils
    miscUtils.deleteUnknownNodes()

def publishCurrentScene(*args, **kwargs):

    sCurScnPath = pm.sceneName()
    damEntity = entityFromScene(sCurScnPath)
    if damEntity:
        proj = damEntity.project
    else:
        proj = projectFromScene(sCurScnPath)

    _, curPubFile = proj.assertEditedVersion(sCurScnPath)

    curPubFile.ensureLocked(autoLock=False)

    try:
        quickSceneCleanUp()
    except Exception, e:
        sConfirm = confirmDialog(title='INFO !',
                                 message="Quick cleanup failed !\n\n{0}".format(toStr(e)),
                                 button=['Continue', 'Cancel'],
                                 defaultButton='Continue',
                                 cancelButton='Cancel',
                                 dismissString='Continue',
                                 icon="information")
        if sConfirm == 'Cancel':
            raise

    scanResults = []
    if damEntity:
        scanResults = dependency_scan.launch(damEntity, modal=True, okLabel="Publish")
        if scanResults is None:
            pm.displayInfo("Canceled !")
            return

    bSgVersion = True
    try:
        infos = curPubFile.beginPublish(sCurScnPath, checkLock=False, **kwargs)
        if infos is None:
            return
        sComment, iNextVers, sgTaskInfo = infos
    except Exception, e:
        curPubFile._abortPublish(e, None, None)
        raise

    if not sgTaskInfo:
        bSgVersion = False

    if damEntity:
        if not publishSceneDependencies(damEntity, scanResults, sComment):
            return

    sSavedScnPath = myasys.saveScene(confirm=False)
    if not sSavedScnPath:
        raise RuntimeError("Could not save your current scene !")

    res = proj.publishEditedVersion(sSavedScnPath,
                                    version=iNextVers,
                                    comment=sComment,
                                    sgTask=sgTaskInfo,
                                    withSgVersion=bSgVersion,
                                    **kwargs)

    pm.displayWarning("Publishing completed !")

    return res

