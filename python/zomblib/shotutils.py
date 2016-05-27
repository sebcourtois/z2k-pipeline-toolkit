import sys
import os

#import itertools as itl

from PySide import QtGui
from PySide.QtGui import QTreeWidgetItemIterator
from PySide.QtCore import Qt

#from pytd.util.qtutils import setWaitCursor
from pytd.util.fsutils import pathJoin
from pytd.util.sysutils import  qtGuiApp
from davos.core.damproject import DamProject

from pytd.gui.dialogs import QuickTreeDialog

def shotsFromShotgun(dialogParent=None):

    global dlg#, sgShotList

    app = qtGuiApp()
    if not app:
        app = QtGui.QApplication(sys.argv)

    proj = initProject()

    sgShotList = proj.listAllSgShots(includeOmitted=False)

    treeDataList = []
    for sgShot in sgShotList:

        sEntiTreePath = pathJoin(sgShot["sg_sequence"]["name"], sgShot["code"])
        roleData = {Qt.UserRole:(0, sgShot)}
        treeDataList.append({"path":sEntiTreePath, "flags":None, "roles":roleData})

    dlg = QuickTreeDialog(dialogParent)
    dlg.resize(300, 800)
    treeWdg = dlg.treeWidget
    #treeWdg.setHeaderLabels(("Shot Tree",))
    treeWdg.headerItem().setHidden(True)

    treeWdg.defaultFlags |= Qt.ItemIsTristate
    treeWdg.defaultRoles = {Qt.CheckStateRole:(0, Qt.Unchecked)}
    treeWdg.createTree(treeDataList)

    bOk = dlg.exec_()
    if bOk:
        flags = (QTreeWidgetItemIterator.Checked | QTreeWidgetItemIterator.Enabled)
        treeIter = QTreeWidgetItemIterator(treeWdg, flags)
        checkedIter = (it.value().data(0, Qt.UserRole) for it in treeIter)

        return bOk, tuple(d for d in checkedIter if d)

    return bOk, tuple()

def initProject(sProjName=""):

    sProject = os.environ["DAVOS_INIT_PROJECT"] if not sProjName else sProjName
    proj = DamProject(sProject)
    print sProject.center(80, "-")

    return proj

def genShotNames(iSeq, *shotNums):
    for n in shotNums:
        yield "sq{:04d}_sh{:04d}a".format(iSeq, n)

if __name__ == "__main__":
    shotsFromShotgun()
