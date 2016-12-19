
import maya.cmds as mc

sGeoGrpList = mc.ls("cwp_*:grp_geo")
if sGeoGrpList:
    mc.select(sGeoGrpList)
else:
    mc.warning("No crowd to select.")
