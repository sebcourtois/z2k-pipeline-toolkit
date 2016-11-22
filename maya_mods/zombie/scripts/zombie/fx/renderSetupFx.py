from dminutes import lighting
reload (lighting)

from dminutes import rendering
reload (rendering)

rendering.setArnoldRenderOptionShot (outputFormat="exr", renderMode='fx3d')
lighting.importFxLights()
