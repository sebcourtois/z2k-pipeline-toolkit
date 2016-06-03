

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

def infosFromScene(scenePath="", fail=True):

    scnInfos = {}

    sCurScnPath = scenePath if scenePath else pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Current scene is untitled.".format(sCurScnPath))

    proj = DamProject.fromPath(sCurScnPath, fail=True)
    pathData = {}
    damEntity = None

    rcFile = proj.entryFromPath(sCurScnPath, fail=fail)
    if rcFile:
        pathData = proj.dataFromPath(rcFile)
        damEntity = proj._entityFromPathData(pathData, fail=fail)
        scnInfos.update(pathData)

    scnInfos.update(project=proj, rc_file=rcFile, dam_entity=damEntity)

    return scnInfos

def assertSceneInfoMatches(scnInfos, sRcName, msg=""):

    if scnInfos.get("resource") != sRcName:
        sMsg = "Current scene is NOT a '{}'.".format(sRcName) if not msg else msg
        raise AssertionError(sMsg)

