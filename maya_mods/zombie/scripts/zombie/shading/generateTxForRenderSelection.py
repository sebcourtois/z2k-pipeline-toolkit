import maya.cmds as mc

from dminutes import shading
reload(shading)

shading.generateTxForRender(fileNodeList = "selection")