
import pymel.core as pm

from davos_maya.tool import reference as myaref
from dminutes.shotconformation import removeRefEditByAttr
reload(myaref)

if not pm.listReferences(loaded=True, unloaded=False):

    sAttrList = ("smoothDrawType", "displaySmoothMesh", "dispResolution")
    removeRefEditByAttr(attr=sAttrList, GUI=False)

    oFileRefList = pm.listReferences(loaded=False, unloaded=True)

    myaref.loadAssetRefsToDefaultFile(dryRun=False, selected=False)

    for oFileRef in oFileRefList:
        if not oFileRef.isLoaded():
            oFileRef.load()

else:
    myaref.loadAssetRefsToDefaultFile(dryRun=False, selected=True)
