
import sys

from davos_maya.core.mrclibrary import MrcLibrary
from davos.gui.assetbrowserwindow import AssetBrowserWindow

WINDOW_NAME = "assetBrowserWin"
mainWin = None

def launch(argv):

    global mainWin

    mainWin = AssetBrowserWindow(WINDOW_NAME)
    mainWin.show()
    mainWin.setProject("zombtest", libraryType=MrcLibrary)

if __name__ == "__main__":
    launch(sys.argv)
