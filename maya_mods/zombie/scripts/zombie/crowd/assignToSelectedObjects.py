
from pytaya.util.qtutils import getWindow

from dminutes import crowd
reload(crowd)

dlg = getWindow("crowdFlavorSelector")
if dlg:
    dlg.showNormal()
    dlg.raise_()
else:
    dlg = crowd.FlavorDialog()
    dlg.show()
