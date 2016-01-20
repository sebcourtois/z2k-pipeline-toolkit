

from dminutes import maya_scene_operations as mop
from pytd.util.sysutils import qtGuiApp

def launch():
    dlg = None
    app = qtGuiApp()
    for w in app.topLevelWidgets():
        if w.objectName() == "SelectRefDialog":
            dlg = w
    if dlg:
        try:
            dlg.refresh()
        except AttributeError:
            pass
        else:
            dlg.showNormal()
            dlg.raise_()
            return

    dlg = mop.SelectRefDialog()
    dlg.show()

launch()
