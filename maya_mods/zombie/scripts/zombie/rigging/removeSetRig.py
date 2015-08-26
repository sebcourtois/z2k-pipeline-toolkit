import pymel.core as pc

from dminutes import modeling
reload(modeling)

sel = pc.ls(sl=True)

if len(sel) == 0:
	pc.warning("Please select your asset root")
else:
	modeling.cleanSet(sel[0])