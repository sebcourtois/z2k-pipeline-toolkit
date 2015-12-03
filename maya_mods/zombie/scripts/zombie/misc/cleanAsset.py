from dminutes import assetconformation
reload (assetconformation)

from dminutes import modeling
reload(modeling)


answer =  mc.confirmDialog( title='Confirm', message="You are about to delete all the node that is not related to the asset structure, delete geometry history and clean the namespaces", button=['Proceed','Cancel'], defaultButton='Proceed', cancelButton='Cancel', dismissString='Cancel' )
	if answer == "Cancel": 
        return


assetconformation.softClean()

modeling.geoGroupDeleteHistory()
modeling.makeAllMeshesUnique(inParent="|asset|grp_geo")
modeling.meshShapeNameConform(inParent = "|asset|grp_geo")