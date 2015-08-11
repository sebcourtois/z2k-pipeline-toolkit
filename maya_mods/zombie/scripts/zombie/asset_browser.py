
import sys

from PySide import QtGui

from davos.core.damproject import DamProject
from davos.gui.assetbrowserwidget import AssetBrowserWidget

from davos_maya.core.mrclibrary import MrcLibrary

mainWin = None

def main(argv):

    global mainWin

    mainWin = QtGui.QMainWindow()
    mainWin.setWindowTitle("Asset Browser")
    view = AssetBrowserWidget(mainWin)
    mainWin.setCentralWidget(view)
    mainWin.resize(1100, 800)
    mainWin.show()

    proj = DamProject("zombillenium", empty=True, libraryType=MrcLibrary)
    if proj:
        proj.init()
        view.setupModelData(proj)
        proj.loadLibraries()

if __name__ == "__main__":
    main(sys.argv)
