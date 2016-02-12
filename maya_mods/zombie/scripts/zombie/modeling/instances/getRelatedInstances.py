import maya.cmds as mc
from dminutes import modeling
reload(modeling)


selectionL = mc.ls(selection=True)
resultD = modeling.getRelatedInstance(selectionL)
mc.select(resultD["resultL"],r=True)
