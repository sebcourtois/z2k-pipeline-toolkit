import maya.cmds as mc

from dminutes import rendering
reload (rendering)

rendering.plugFinalLayoutCustomShader(dmnToonList=[], dmnInput = "dmnMask08")