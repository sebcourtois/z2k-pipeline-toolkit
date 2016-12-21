from dminutes import finalLayout
reload (finalLayout)

from dminutes import rendering
reload (rendering)

rendering.setArnoldRenderOptionShot (outputFormat="jpg", renderMode = 'finalLayout')

finalLayout.importFinalLayoutLight()
finalLayout.createRenderLayerLegacy(layerName="lay_finalLayout_00",lightL=["lgt_finalLayout_directional"], setMeshCacheL=[])
finalLayout.layerOverrideToonWeightOff(dmnToonList=[], layerName = "lay_finalLayout_00", gui= True)
finalLayout.fixDeferLoad()
#finalLayout.layerOverrideFLCustomShader(dmnToonList=[], dmnInput = "dmnMask08", layerName = "lay_finalLayout_00",gui= True)



