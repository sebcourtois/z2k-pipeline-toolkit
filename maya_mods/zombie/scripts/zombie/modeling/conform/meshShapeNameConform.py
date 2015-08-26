import maya.cmds as mc

from dminutes import modeling
reload(modeling)

modeling.meshShapeNameConform(inParent = "|asset|grp_geo")


