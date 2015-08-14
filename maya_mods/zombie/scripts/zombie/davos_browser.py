
import sys

from PySide import QtGui

from davos.core.damproject import DamProject
#from davos.gui.assetbrowserwindow import AssetBrowserWindow

#from davos_maya.core.mrclibrary import MrcLibrary

mainWin = None

def launch(argv):

    global mainWin

    mainWin = AssetBrowserWindow(WINDOW_NAME)
    mainWin.show()
    mainWin.setProject("zombtest", libraryType=MrcLibrary)

if __name__ == "__main__":
    launch(sys.argv)
