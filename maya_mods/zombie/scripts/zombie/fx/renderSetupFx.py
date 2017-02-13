from dminutes import lighting
reload (lighting)

from dminutes import rendering
reload (rendering)

from dminutes.fx import setFxSettings
reload (setFxSettings)

rendering.setArnoldRenderOptionShot (outputFormat="exr", renderMode='fx3d')
setFxSettings.setFxSettings()
lighting.importFxLights()
rendering.fixDeferLoad()
