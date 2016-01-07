

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
        raise ValueError("Invalid scene name: '{}'".format(sCurScnPath))

    return DamProject.fromPath(sCurScnPath, fail=True)

def entityFromScene(scenePath="", fail=True):

    sCurScnPath = scenePath if scenePath else pm.sceneName()
    if not sCurScnPath:
        raise ValueError("Invalid scene name: '{}'".format(sCurScnPath))

    proj = DamProject.fromPath(sCurScnPath, fail=True)
    damEntity = proj.entityFromPath(sCurScnPath, fail=fail)

    return damEntity
