
import maya.cmds as mc
from dminutes import geocaching
reload(geocaching)

sGeoGrpList, _ = geocaching._confirmProcessing("Select 'grp_geo'", confirm=False)
if sGeoGrpList:
    mc.select(sGeoGrpList)
else:
    mc.warning("No 'grp_geo' to select.")



