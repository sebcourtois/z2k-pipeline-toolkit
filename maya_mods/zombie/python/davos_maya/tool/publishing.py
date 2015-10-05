
import os

#from pytd.util.logutils import logMsg
from pytaya.core import system as myasys

from davos.core.damproject import DamProject
from pytd.gui.dialogs import confirmDialog
from pytd.util.logutils import logMsg


def publishCurrentScene(*args, **kwargs):

    sProject = os.environ["DAVOS_INIT_PROJECT"]
    proj = DamProject(sProject)

    sConfirm = confirmDialog(title="WARNING !",
                             message="Are you sure ?",
                             button=("Publish...", "Cancel"),
                             defaultButton="Cancel",
                             cancelButton="Cancel",
                             dismissString="Cancel",
                            )

    if sConfirm == "Cancel":
        logMsg("Cancelled !" , warning=True)
        return

    sScenePath = myasys.saveScene(confirm=False)
    if not sScenePath:
        raise RuntimeError("Could not save your current scene !")

    return proj.publishEditedVersion(sScenePath, **kwargs)

