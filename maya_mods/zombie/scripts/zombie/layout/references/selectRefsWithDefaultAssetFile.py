

from davos_maya.tool.reference import SelectRefDialog
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

    dlg = SelectRefDialog()
    dlg.show()

launch()
