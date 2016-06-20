

import os
import os.path as osp

import maya.cmds as mc
import pymel.core as pm
import pymel.util as pmu

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

def setMayaProject(sProjName, sEnvVar):

    if not sProjName:
        raise ValueError("Invalid project name: '{}'".format(sProjName))

    if not sEnvVar:
        raise ValueError("Invalid env. variable: '{}'".format(sEnvVar))

    sMayaProjsLoc = osp.dirname(osp.normpath(mc.workspace(q=True, rd=True)))
    sMayaProjPath = osp.join(sMayaProjsLoc, sProjName)

    if not osp.exists(sMayaProjPath):
        os.mkdir(sMayaProjPath)

    mc.workspace(update=True)
    mc.workspace(sProjName, openWorkspace=True)

    if not mc.workspace(fileRuleEntry="movie"):
        mc.workspace(fileRule=("movie", "captures"))
        mc.workspace(saveWorkspace=True)

    if not mc.workspace(fileRuleEntry="alembicCache"):
        mc.workspace(fileRule=("alembicCache", "cache/alembic"))
        mc.workspace(saveWorkspace=True)

    pmu.putEnv(sEnvVar, sMayaProjPath.replace("\\", "/"))

    return sMayaProjPath

