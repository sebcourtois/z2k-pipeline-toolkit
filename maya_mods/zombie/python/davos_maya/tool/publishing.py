

import pymel.core as pm

#from pytd.util.logutils import logMsg
from pytaya.core import system as myasys

from davos.core.damproject import DamProject
from pytd.gui.dialogs import confirmDialog
#from pytd.util.logutils import logMsg
from pytaya.core.general import lsNodes
from pytd.util.fsutils import pathResolve

from .general import entityFromScene

def publishSceneDependencies(proj, sCurScnPath, **kwargs):

    fileNodeList = lsNodes("*", type='file', not_rn=True)
    fileTexItems = []
    for fileNode in fileNodeList:

        p = fileNode.getAttr("fileTextureName")
        if not p:
            continue

        sAbsPath = pathResolve(p)
        privFile = proj.entryFromPath(sAbsPath)
        if not privFile:
            continue

        if privFile.isPublic():
            continue

        fileTexItems.append((fileNode, privFile))

    sTexPathList = tuple(f.absPath() for _, f in fileTexItems)
    if sTexPathList:

        sConfirm = confirmDialog(title="QUESTION !",
                                 message="Publish Textures ?",
                                 button=("Yes", "No"),
                                 defaultButton="No",
                                 cancelButton="No",
                                 dismissString="No",
                                 icon="question",
                                )
        if sConfirm == "No":
            return

        publishedFileItems = proj.publishDependencies("texture_dep", sCurScnPath,
                                                      sTexPathList, **kwargs)

        fileNodes = (n for n, _ in fileTexItems)
        pubFiles = (f for f, _ in publishedFileItems)

        for fileNode, pubFile in zip(fileNodes, pubFiles):
            fileNode.setAttr("fileTextureName", pubFile.envPath())

def publishCurrentScene(*args, **kwargs):

    sCurScnPath = pm.sceneName()
    damEntity = entityFromScene(sCurScnPath)
    proj = damEntity.project

    _, curPubFile = proj.assertEditedVersion(sCurScnPath)

    bSgVersion = True
    try:
        infos = curPubFile.beginPublish(sCurScnPath, **kwargs)
        sComment, iNextVers, sgTaskInfo = infos
    except Exception, e:
        curPubFile._abortPublish(e, None, None)
        raise

    if not sgTaskInfo:
        bSgVersion = False

    #publishSceneDependencies(proj, sCurScnPath, comment=sComment)

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

