

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
from pytd.util.sysutils import inDevMode

def publishSceneDependencies(damEntity, scanResults, sComment, **kwargs):

    bDryRun = kwargs.pop("dryRun", False)

    proj = damEntity.project

    sTexPathList = []
    fileNodesList = []
    sBuddyFileList = []
    for result in scanResults:

        if not result["publish_ok"]:
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

        for fileNodes, pubFile in zip(fileNodesList, pubFiles):
            sEnvPath = pubFile.envPath("ZOMB_TEXTURE_PATH")
            print sEnvPath
            for n in fileNodes:

                sNodeName = n.name()
                if sNodeName in sUpdNodeList:
                    continue

                if not bDryRun:
                    n.setAttr("fileTextureName", sEnvPath)

                sUpdNodeList.append(sNodeName)
                print "    ", sNodeName
            print ""


    if not sBuddyFileList:
        return

    with NamedTemporaryFile(suffix=".txt", delete=False) as tmpFile:
        tmpFile.write("\n".join(sBuddyFileList))

    p = publish_dependencies.__file__
    sCmdArgs = [r"C:\Python27\python.exe",
                p[:-1]if p.endswith("c") else p,
                proj.name, "texture_dep",
                damEntity.sgEntityType.lower(),
                damEntity.name,
                tmpFile.name,
                sComment,
                "--dryRun", str(int(bDryRun)),
                ]

    subprocess.Popen(sCmdArgs)

    return (not bDryRun)

def publishCurrentScene(*args, **kwargs):

    sCurScnPath = pm.sceneName()
    damEntity = entityFromScene(sCurScnPath)
    proj = damEntity.project

    _, curPubFile = proj.assertEditedVersion(sCurScnPath)

    if inDevMode():
        scanResults = dependency_scan.launch(damEntity, modal=True)
        if scanResults is None:
            pm.displayInfo("Canceled")
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

    if inDevMode():
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

    pm.displayInfo("Publishing completed !")

    return res

