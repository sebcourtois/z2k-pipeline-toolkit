
import sys
import os

from PySide.QtCore import Qt

from davos.gui.assetbrowserwindow import AssetBrowserWindow

#from pytd.util.sysutils import inDevMode
from pytd.util.qtutils import getWidget

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from davos.core.utils import loadPrefs

MAIN_WIN = None

class MayaAssetBrowserWindow(MayaQWidgetDockableMixin, AssetBrowserWindow):

    def __init__(self, parent=None):
        super(MayaAssetBrowserWindow, self).__init__(parent=parent)

def kill():

    global MAIN_WIN

    if MAIN_WIN:

        MAIN_WIN.setAttribute(Qt.WA_DeleteOnClose, True)
        MAIN_WIN.close()
        MAIN_WIN = None

        return True

    return False

def launch(argv):

    global MAIN_WIN

    MAIN_WIN = getWidget("AssetBrowserWin")
    if MAIN_WIN:
        MAIN_WIN.showNormal()
        MAIN_WIN.raise_()
    else:

        loadPrefs()

        MAIN_WIN = MayaAssetBrowserWindow()
        MAIN_WIN.show(dockable=False)

        sProject = os.environ.get("DAVOS_INIT_PROJECT")
        if sProject:
            MAIN_WIN.setProject(sProject)

if __name__ == "__main__":
    launch(sys.argv)

