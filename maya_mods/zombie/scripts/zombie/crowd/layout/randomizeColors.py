
import maya.cmds as mc

from dminutes import geocaching
reload(geocaching)

from dminutes import crowd
reload(crowd)

sGeoGrpList, _ = geocaching._confirmProcessing("Select active cache", selected=True,
                                               confirm=False, regexp="^cwp_")
if sGeoGrpList:
    crowd.switchColors(sGeoGrpList)
else:
    mc.warning("No crowd selected.")
