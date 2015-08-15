import maya.cmds as mc

from dminutes import modeling
reload(modeling)

modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")