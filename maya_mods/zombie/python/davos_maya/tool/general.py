

import os

import pymel.core as pm

from davos.core.damproject import DamProject


def loadProject():

    bBatchMode = pm.about(batch=True)
    proj = DamProject(os.environ["DAVOS_INIT_PROJECT"], empty=bBatchMode)
    proj.loadEnviron()

def projectFromScene(scenePath=""):

    sCurScnPath = scenePath if scenePath else pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    return DamProject.fromPath(sCurScnPath, fail=True)

def entityFromScene(scenePath="", fail=True):

    sCurScnPath = scenePath if scenePath else pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    proj = DamProject.fromPath(sCurScnPath, fail=True)
    damEntity = proj.entityFromPath(sCurScnPath, fail=fail)

    return damEntity

def assertCurrentSceneMatches(sRcName, msg=""):

    sCurScnPath = pm.sceneName()
    damEntity = entityFromScene(sCurScnPath)
    privScnFile = damEntity.getLibrary("private").getEntry(sCurScnPath, dbNode=False)
    pubScnFile = privScnFile.getPublicFile()

    if pubScnFile != damEntity.getResource("public", sRcName, dbNode=False):
        sMsg = "Current scene is NOT a '{}'.".format(sRcName) if not msg else msg
        raise AssertionError(sMsg)

    return damEntity, privScnFile, pubScnFile
