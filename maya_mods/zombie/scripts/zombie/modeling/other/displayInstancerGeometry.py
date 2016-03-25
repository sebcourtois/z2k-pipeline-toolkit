import maya.cmds as mc
from dminutes import assetconformation
reload (assetconformation)


assetconformation.setInstancerLod(inParent = mc.ls(selection=True), lod=0)
