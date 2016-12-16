

import maya.cmds as mc

from dminutes import geocaching
reload(geocaching)

sGeoGrpList, _ = geocaching._confirmProcessing("Select active cache", confirm=False,
                                               regexp="^cwp_", selected=True)
sAbcNodeList = []
for sGeoGrp in sGeoGrpList:

    if not mc.objExists(sGeoGrp + ".animationChoice"):
        continue

    sNodeList = mc.listConnections(sGeoGrp + ".animationChoice", s=False, d=True, type="choice")
    if not sNodeList:
        continue

    sChoiceNode = sNodeList[0]
    iChoiceIdx = mc.getAttr(sGeoGrp + ".animationChoice")

    sNodeList = mc.listConnections(sChoiceNode + ".input[{}]".format(iChoiceIdx),
                                   s=True, d=False, type="AlembicNode")
    if not sNodeList:
        continue

    sAbcNodeList.append(sNodeList[0])

if sAbcNodeList:
    mc.select(sAbcNodeList)
else:
    mc.warning("No active cache to select.")


