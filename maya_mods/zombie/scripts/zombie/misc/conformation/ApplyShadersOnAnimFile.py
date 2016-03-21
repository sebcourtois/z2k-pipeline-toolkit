
from dminutes import miscUtils
reload (miscUtils)

import maya.cmds as mc
import pymel.core as pm
from dminutes import assetconformation
reload (assetconformation)
      
r2a = assetconformation.Asset_File_Conformer()
mc.refresh(suspend = True)

if r2a.assetFileType != "anim":
	raise ValueError( "Working file must be an '_anim' file, operation canceled")

r2a.cleanFile()
r2a.loadFile(sourceFile ="renderRef" , reference = False)

print "#### {:>7}: target is: {}".format("Info",r2a.assetName+"_"+r2a.assetFileType)
r2a.initSourceTargetList()
r2a.checkSourceTargetTopoMatch()

if r2a.sourceTargetListMatch and r2a.sourceTargetTopoMatch:
	r2a.smoothPolyDisplay(r2a.targetList)
	r2a.transferRenderAttr()
	r2a.transferUV()
	r2a.disconnectAllShadEng(r2a.targetList)
	r2a.transferSG()
	r2a.deleteUnusedShadingNodes()
	r2a.removeNameSpaceFromShadNodes(r2a.targetList)
	r2a.cleanFile()
	mc.refresh()
	assetconformation.fixMaterialInfo()
	r2a.deleteUnusedShadingNodes()

else:
	r2a.cleanFile()
	#raise ValueError( "Asset is not conform, please fix and run the script again")
	mc.confirmDialog( title='Confirm', message="Asset is not conform, please fix and run the script again", button=['Ok'], defaultButton='Ok',)

mc.refresh(suspend = False)





