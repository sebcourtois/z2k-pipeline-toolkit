
from pytd.util.qtutils import getWidget

from dminutes import crowd

dlg = getWidget("CrowdFlavorSelector")
if dlg:
    dlg.showNormal()
    dlg.raise_()
else:
    reload(crowd)
    dlg = crowd.FlavorDialog()
    dlg.show()
