
import random

import maya.cmds as mc

from dminutes import crowd
from dminutes import geocaching

reload(crowd)
reload(geocaching)

sGeoGrpList, _ = geocaching._confirmProcessing("Randomize anim offset", confirm=False,
                                               regexp="^cwp_", selected=None, fromShapes=False)

sAbcNodeList = tuple(crowd.iterActiveCaches(sGeoGrpList))
if sAbcNodeList:

    res = mc.promptDialog(title='Please...',
                          message='Enter random range (or just 0 to reset offsets): ',
                          button=['OK', 'Cancel'],
                          defaultButton='OK',
                          cancelButton='Cancel',
                          dismissString='Cancel',
                          scrollableField=True,
                          text="start stop step")

    if res == 'OK':
        sArgs = mc.promptDialog(query=True, text=True)
        args = tuple(int(s) for s in sArgs.strip().split())
        if len(args) == 1:
            v = args[0]
            for sAbcNode in sAbcNodeList:
                mc.setAttr(sAbcNode + ".offset", v)
        elif args:
            for sAbcNode in sAbcNodeList:
                offset = mc.getAttr(sAbcNode + ".offset")
                mc.setAttr(sAbcNode + ".offset", offset + random.randrange(*args))

    mc.select(sAbcNodeList)
else:
    mc.warning("No active cache on which to set offet.")
