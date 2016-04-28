from dminutes import miscUtils
reload (miscUtils)

import maya.cmds as mc
import pymel.core as pm
from dminutes import assetconformation
reload (assetconformation)
import maya.utils as mu

miscUtils.cleanLayout()

def r2aPrepareAnim():      
	r2a = assetconformation.Asset_File_Conformer()
	mc.refresh(suspend = True)

	try: 
		if r2a.assetFileType != "render":
			raise ValueError( "Working file must be an 'render' file, operation canceled")

		r2a.cleanFile()
		r2a.loadFile(sourceFile ="animRef" , reference = False)

		mc.delete(r2a.sourceFile+":asset",constructionHistory=True)
		mc.delete(r2a.sourceFile+":asset|"+r2a.sourceFile+":grp_rig")
		miscUtils.deleteAllColorSet()


		print "#### {:>7}: target is: {}".format("Info",r2a.assetName+"_"+r2a.assetFileType)

		targetObjects = mc.ls(mc.sets("animRef:set_meshCache",q=1),l=1)
		r2a.initSourceTargetList(sourceFile = "root", targetObjects = targetObjects)
		r2a.checkSourceTargetTopoMatch()

		r2a.smoothPolyDisplay(r2a.targetList,shapeOrigOnly = False)
		r2a.transferRenderAttr()
		r2a.transferUV(sampleSpace = 0)
		# r2a.disconnectAllShadEng(r2a.targetList)
		# r2a.transferSG()
		# r2a.deleteUnusedShadingNodes()
		# r2a.removeNameSpaceFromShadNodes(r2a.targetList)
		# r2a.cleanFile()
		mc.refresh()
		#assetconformation.fixMaterialInfo()
		#r2a.deleteUnusedShadingNodes()



	finally:
		mc.refresh(suspend = False)


mu.executeDeferred(r2aPrepareAnim)


# sampleSpace: Selects which space the attribute transfer is performed in. 
# 0 is world space, (default)
# 1 is model space, 
# 4 is component-based, 
# 5 is topology-based


