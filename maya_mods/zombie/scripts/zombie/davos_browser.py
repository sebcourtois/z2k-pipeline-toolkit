
import sys

from PySide.QtCore import Qt

from davos_maya.core.mrclibrary import MrcLibrary
from davos.gui.assetbrowserwindow import AssetBrowserWindow

from pytd.util.sysutils import inDevMode
from pytaya.util.qtutils import getWindow

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

mainWin = None

class MayaHookWindow(MayaQWidgetDockableMixin, AssetBrowserWindow):

    def __init__(self, parent=None):
        super(MayaHookWindow, self).__init__(parent=parent)


def launch(argv):

    global mainWin

    mainWin = getWindow("AssetBrowserWin")
    if mainWin:
        mainWin.showNormal()
        #mainWin.raise_()
    else:
        mainWin = MayaHookWindow()
        mainWin.show(dockable=False)

        sProject = "zombtest" if inDevMode() else "zombillenium"
        mainWin.setProject(sProject)

if __name__ == "__main__":
    launch(sys.argv)

