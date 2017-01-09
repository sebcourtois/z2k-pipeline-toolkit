

import maya.cmds as mc

from dminutes import crowd
from dminutes import geocaching

reload(crowd)
reload(geocaching)

sGeoGrpList, _ = geocaching._confirmProcessing("Select active cache", confirm=False,
                                               regexp="^cwp_", selected=True)

sAbcNodeList = tuple(crowd.iterActiveCaches(sGeoGrpList))
if sAbcNodeList:
    mc.select(sAbcNodeList)
else:
    mc.warning("No active cache to select.")

