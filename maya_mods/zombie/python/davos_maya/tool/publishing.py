
import os

#from pytd.util.logutils import logMsg
from pytaya.core import system as myasys

from davos.core.damproject import DamProject


def publishCurrentScene(*args):

    sProject = os.environ["DAVOS_INIT_PROJECT"]
    proj = DamProject(sProject)

    sScenePath = myasys.saveScene(confirm=False)
    if not sScenePath:
        raise RuntimeError("Could not save your current scene !")

    proj.publishEditedVersion(sScenePath)

