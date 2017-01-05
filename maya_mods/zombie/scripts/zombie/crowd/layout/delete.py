

import maya.cmds as mc
import pymel.core as pm

#from pytaya.util import apiutils as myapi

from dminutes import geocaching, crowd
reload(geocaching)
reload(crowd)

def delete():
    sGeoGrpList, _ = geocaching._confirmProcessing("Delete", selected=True, confirm=True,
                                                   regexp="^cwp_", fromShapes=False)
    #sGeoGrpList = tuple(s for s in sGeoGrpList if mc.referenceQuery(s, isNodeReferenced=True))

    if not sGeoGrpList:
        mc.warning("No crowd to delete.")
        return

    crowd.delete(sGeoGrpList)

delete()
