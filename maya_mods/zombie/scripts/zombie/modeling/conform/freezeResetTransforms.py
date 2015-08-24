import maya.cmds as mc

from dminutes import modeling
reload(modeling)


modeling.freezeResetTransforms(inParent = "|asset|grp_geo")

