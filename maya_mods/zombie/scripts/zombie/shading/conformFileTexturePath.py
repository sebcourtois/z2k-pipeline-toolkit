import maya.cmds as mc

from dminutes import shading
reload(shading)

shading.conformTexturePath(inVerbose = True, inConform = True, inCopy =False)