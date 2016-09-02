import maya.cmds as mc
from dminutes import shotconformation
reload (shotconformation)



selectionL = mc.ls(selection = True)

shotconformation.releaseShotAsset(gui = True ,toReleaseL = selectionL, astPrefix = "fx3", dryRun=False)
