
import os
import subprocess
from tempfile import NamedTemporaryFile

import pymel.core as pm

#from pytd.util.logutils import logMsg
from pytaya.core import system as myasys

#from pytd.gui.dialogs import confirmDialog
#from pytd.util.logutils import logMsg
#from pytaya.core.general import lsNodes
#from pytd.util.fsutils import pathResolve

from davos.tools import publish_dependencies

from .general import entityFromScene
from davos_maya.tool import dependency_scan
from pytd.util.sysutils import toStr, inDevMode

bDevDryRun = False

def publishSceneDependencies(damEntity, scanResults, sComment, **kwargs):

    bDryRun = kwargs.pop("dryRun", False if not inDevMode() else bDevDryRun)

    proj = damEntity.project

    sTexPathList = []
    fileNodesList = []
    sBuddyFileList = []
    for result in scanResults:

        if not result["publishable"]:
            continue

        fileNodes = result["file_nodes"]
        if fileNodes:
            sTexPathList.append(result["abs_path"])
            fileNodesList.append(fileNodes)
            sBuddyFileList.extend(result["buddy_files"])

    if sTexPathList:
        publishedFileItems = proj.publishDependencies("texture_dep",
                                                      damEntity,
                                                      sTexPathList,
                                                      sComment,
                                                      dryRun=bDryRun,
                                                      **kwargs)
        pubFiles = (f for f, _ in publishedFileItems)

        sUpdNodeList = []
        sMsgFmt = "\nUpdating {} path: \nfrom '{}'\n  to '{}'"

        for fileNodes, pubFile in zip(fileNodesList, pubFiles):

            sEnvPath = pubFile.envPath("ZOMB_TEXTURE_PATH")

            for fileNode in fileNodes:

                sNodeName = fileNode.name()
                if sNodeName in sUpdNodeList:
                    continue

                sMsg = (sMsgFmt.format(repr(fileNode),
                                       fileNode.getAttr("fileTextureName"),
                                       sEnvPath))
                print sMsg

                if not bDryRun:
                    fileNode.setAttr("fileTextureName", sEnvPath)

                sUpdNodeList.append(sNodeName)

    if not sBuddyFileList:
        return (not bDryRun)

    bUseSubprocess = False
    if not bUseSubprocess:

        print "\n" + " Publishing associated files: .psd, .tx, etc... ".center(100, '-')

        publishedFileItems = proj.publishDependencies("texture_dep",
                                                      damEntity,
                                                      sBuddyFileList,
                                                      sComment,
                                                      dryRun=bDryRun,
                                                      **kwargs)
    else:
        sMsg = """
Opening a new process to publish associated files: .psd, .tx, etc...
    """
        pm.displayWarning(sMsg)

        with NamedTemporaryFile(suffix=".txt", delete=False) as tmpFile:
            tmpFile.write("\n".join(sBuddyFileList))

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

    return (not bDryRun)

def publishCurrentScene(*args, **kwargs):

    sCurScnPath = pm.sceneName()
    damEntity = entityFromScene(sCurScnPath)
    proj = damEntity.project

    _, curPubFile = proj.assertEditedVersion(sCurScnPath)

    scanResults = dependency_scan.launch(damEntity, modal=True)
    if scanResults is None:
        pm.displayInfo("Canceled !")
        return

    bSgVersion = True
    try:
        infos = curPubFile.beginPublish(sCurScnPath, **kwargs)
        sComment, iNextVers, sgTaskInfo = infos
    except Exception, e:
        curPubFile._abortPublish(e, None, None)
        raise

    if not sgTaskInfo:
        bSgVersion = False

    pm.mel.ScriptEditor()
    pm.mel.handleScriptEditorAction("maximizeHistory")

    if not publishSceneDependencies(damEntity, scanResults, sComment):
        return

    sSavedScnPath = myasys.saveScene(confirm=False)
    if not sSavedScnPath:
        raise RuntimeError("Could not save your current scene !")

    res = proj.publishEditedVersion(sCurScnPath,
                                    version=iNextVers,
                                    comment=sComment,
                                    sgTask=sgTaskInfo,
                                    withSgVersion=bSgVersion,
                                    **kwargs)

    pm.displayWarning("Publishing completed !")

    return res

