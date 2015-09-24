
import os

import pymel.core as pm

from davos.core.damproject import DamProject

def publishCurrentScene(*args):

    sProject = os.environ["DAVOS_INIT_PROJECT"]
    proj = DamProject(sProject)

    sScnPath = pm.sceneName()
    proj.publishEditedVersion(sScnPath)

