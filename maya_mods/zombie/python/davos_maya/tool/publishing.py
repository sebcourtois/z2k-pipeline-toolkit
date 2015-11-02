

import pymel.core as pm

#from pytd.util.logutils import logMsg
from pytaya.core import system as myasys

#from pytd.gui.dialogs import confirmDialog
#from pytd.util.logutils import logMsg
#from pytaya.core.general import lsNodes
#from pytd.util.fsutils import pathResolve

from .general import entityFromScene
from davos_maya.tool import dependency_scan
from pytd.util.logutils import logMsg
from pytd.util.sysutils import inDevMode

def publishSceneDependencies(damEntity, sCurScnPath, scanResults, **kwargs):

    bDryRun = kwargs.pop("dryRun", False)

    proj = damEntity.project

    sTexPathList = []
    fileNodesList = []
    for result in scanResults:

        if not result["publish_ok"]:
            continue

        fileNodes = result["file_nodes"]
        if fileNodes:
            sTexPathList.append(result["abs_path"])
            fileNodesList.append(fileNodes)

    if sTexPathList:
        publishedFileItems = proj.publishDependencies("texture_dep",
                                                      sCurScnPath,
                                                      sTexPathList,
                                                      entity=damEntity,
                                                      dryRun=bDryRun,
                                                      **kwargs)
        pubFiles = (f for f, _ in publishedFileItems)

        sUpdNodeList = []

        for fileNodes, pubFile in zip(fileNodesList, pubFiles):
            sEnvPath = pubFile.envPath("ZOMB_TEXTURE_PATH")
            print sEnvPath
            for fn in fileNodes:

                sNodeName = fn.name()
                if sNodeName in sUpdNodeList:
                    continue

                if not bDryRun:
                    fn.setAttr("fileTextureName", sEnvPath)

                sUpdNodeList.append(sNodeName)
                print "    ", sNodeName
            print ""

def publishCurrentScene(*args, **kwargs):

    sCurScnPath = pm.sceneName()
    damEntity = entityFromScene(sCurScnPath)
    proj = damEntity.project

    _, curPubFile = proj.assertEditedVersion(sCurScnPath)

    if inDevMode():
        scanResults = dependency_scan.launch(damEntity, modal=True)
        if scanResults is None:
            logMsg("Canceled", warning=True)
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
        publishSceneDependencies(damEntity, sCurScnPath, scanResults, comment=sComment)

    sSavedScnPath = myasys.saveScene(confirm=False)
    if not sSavedScnPath:
        raise RuntimeError("Could not save your current scene !")

    res = proj.publishEditedVersion(sCurScnPath,
                                    version=iNextVers,
                                    comment=sComment,
                                    sgTask=sgTaskInfo,
                                    withSgVersion=bSgVersion,
                                     **kwargs)
    return res

