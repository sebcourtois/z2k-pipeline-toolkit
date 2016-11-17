from dminutes import finalLayout
reload (finalLayout)

from dminutes import rendering
reload (rendering)

rendering.setArnoldRenderOptionShot (outputFormat="exr", renderMode='fx3d')
finalLayout.importFinalLayoutLight()
