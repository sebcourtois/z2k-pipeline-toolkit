

import pymel.core as pm
oSelList = pm.selected()

if len(oSelList) != 2:
    raise RuntimeError("Please, substitute first selected curve with second one.")

oSrcCrv = oSelList[1]
oTrgtCrv = oSelList[0]
oSrcCrv.getShape().attr("worldSpace[0]") >> oTrgtCrv.getShape().attr("create")

mtx = pm.xform(oSrcCrv, q=True, ws=True, m=True)
pm.xform(oTrgtCrv, ws=True, m=mtx)

oTrgtCrv.setAttr("visibility", False)
pm.select(oSrcCrv)