
import sys

from davos_maya.core.mrclibrary import MrcLibrary
from davos.gui.assetbrowserwindow import AssetBrowserWindow
from pytd.util.sysutils import inDevMode

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

WINDOW_NAME = "assetBrowserWin"
mainWin = None

class MayaHookWindow(MayaQWidgetBaseMixin, AssetBrowserWindow):

    def __init__(self, parent=None):
        super(MayaHookWindow, self).__init__(parent=parent)

def launch(argv):

    global mainWin

    mainWin = MayaHookWindow()
    mainWin.show()
    sProject = "zombtest" if inDevMode() else "zombillenium"
    mainWin.setProject(sProject, libraryType=MrcLibrary)

if __name__ == "__main__":
    launch(sys.argv)
