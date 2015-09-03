import maya.cmds as mc

from dminutes import assetconformation
reload(assetconformation)

assetconformation.checkGroupNamingConvention(inParent = "|asset|grp_geo")

