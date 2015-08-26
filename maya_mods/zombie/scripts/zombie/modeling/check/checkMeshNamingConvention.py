import maya.cmds as mc

from dminutes import modeling
reload(modeling)

modeling.checkMeshNamingConvention(inParent = "|asset|grp_geo")

