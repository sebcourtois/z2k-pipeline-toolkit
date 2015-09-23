
import sys
import os

from PySide.QtCore import Qt

from davos.gui.assetbrowserwindow import AssetBrowserWindow

#from pytd.util.sysutils import inDevMode
from pytaya.util.qtutils import getWindow

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

mainWin = None

class MayaHookWindow(MayaQWidgetDockableMixin, AssetBrowserWindow):

    def __init__(self, parent=None):
        super(MayaHookWindow, self).__init__(parent=parent)


def kill():

    global mainWin

    if mainWin:

        mainWin.setAttribute(Qt.WA_DeleteOnClose, True)
        mainWin.close()
        mainWin = None

        return True

    return False

def launch(argv):

    global mainWin

    mainWin = getWindow("AssetBrowserWin")
    if mainWin:
        mainWin.showNormal()
        #mainWin.raise_()
    else:
        mainWin = MayaHookWindow()
        mainWin.show(dockable=False)

        sProject = os.environ.get("DAVOS_INIT_PROJECT")
        if sProject:
            mainWin.setProject(sProject)

if __name__ == "__main__":
    launch(sys.argv)

