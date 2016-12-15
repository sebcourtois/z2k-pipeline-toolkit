
import maya.cmds as mc

from dminutes import geocaching
reload(geocaching)

from dminutes import crowd
reload(crowd)

sGeoGrpList, _ = geocaching._confirmProcessing("Select active cache", confirm=False,
                                               regexp="^cwp_", selected=True)
if sGeoGrpList:
    #mc.select(mc.ls(mc.ls(sGeoGrpList, dag=True), type="locator"))
    crowd.switchColors(sGeoGrpList)
else:
    mc.warning("No crowd selected.")
