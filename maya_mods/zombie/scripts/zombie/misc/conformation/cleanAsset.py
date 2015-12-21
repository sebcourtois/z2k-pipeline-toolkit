import maya.cmds as mc

from dminutes import modeling
reload(modeling)

from dminutes import assetconformation
reload(assetconformation)

from dminutes import rendering
reload (rendering)

from dminutes import miscUtils
reload (miscUtils)





answer =  mc.confirmDialog( title='Confirm', message="You are about to delete all the nodes that are not related to the asset structure,\n delete geometry history, all the colors sets and clean the namespaces", button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
if answer != "Cancel": 
	rendering.deleteAovs()
	assetconformation.softClean()
	modeling.geoGroupDeleteHistory()
	modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
	modeling.meshShapeNameConform(inParent = "|asset|grp_geo")
	miscUtils.deleteUnknownNodes()
	miscUtils.deleteAllColorSet()