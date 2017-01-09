
import random

import maya.cmds as mc

from dminutes import crowd
from dminutes import geocaching

reload(crowd)
reload(geocaching)

sGeoGrpList, _ = geocaching._confirmProcessing("Randomize anim offset", confirm=True,
                                               regexp="^cwp_", selected=None, fromShapes=False)

sAbcNodeList = tuple(crowd.iterActiveCaches(sGeoGrpList))
if sAbcNodeList:

    for sAbcNode in sAbcNodeList:
        mc.setAttr(sAbcNode + ".speed", round(random.uniform(1.00, 2.25), 2))

    mc.select(sAbcNodeList)
else:
    mc.warning("No active cache on which to set speed.")
