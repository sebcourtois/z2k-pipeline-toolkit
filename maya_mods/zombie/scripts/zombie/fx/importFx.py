import maya.cmds as mc
from dminutes import shotconformation
reload (shotconformation)




shotconformation.referenceShotAsset(gui = True, astPrefix = "fx3", critical= False)

grpFxL =mc.ls("shot|grp_fx")
unparentedFx = mc.ls("|fx3_*:asset", type="transform")
if grpFxL and unparentedFx:
    mc.parent(unparentedFx, "shot|grp_fx")