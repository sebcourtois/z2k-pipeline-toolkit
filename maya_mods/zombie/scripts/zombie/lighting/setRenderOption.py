
import maya.cmds as mc

from dminutes import rendering
reload (rendering)

rendering.setArnoldRenderOptionShot (outputFormat="exr", renderMode = 'render')
rendering.fixDeferLoad()
rendering.fixToonWeight()
rendering.fixCrowdShadowOpacity()
