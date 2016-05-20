
import maya.cmds as mc

from dminutes import rendering
reload (rendering)

rendering.setArnoldRenderOptionShot (outputFormat="png", renderMode = 'finalLayout')