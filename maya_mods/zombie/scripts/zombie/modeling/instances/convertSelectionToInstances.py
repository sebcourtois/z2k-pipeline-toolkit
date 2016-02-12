import maya.cmds as mc

from dminutes import modeling
reload(modeling)


selectionL = mc.ls(selection=True)
modeling.convertObjToInstance(selectionL)