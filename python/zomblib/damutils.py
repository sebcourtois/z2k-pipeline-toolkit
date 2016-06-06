
import sys
import os

from PySide import QtGui
from PySide.QtGui import QTreeWidgetItemIterator
from PySide.QtCore import Qt

#from pytd.util.qtutils import setWaitCursor
from pytd.util.fsutils import pathJoin
from pytd.util.sysutils import  qtGuiApp, inDevMode
from pytd.gui.dialogs import QuickTreeDialog

from davos.core.damproject import DamProject

def shotsFromShotgun(project=None, dialogParent=None):

    global dlg

    app = qtGuiApp()
    if not app:
        app = QtGui.QApplication(sys.argv)

    proj = initProject() if not project else project

    sgShotList = proj.listAllSgShots(includeOmitted=inDevMode())

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

    while True:
        bOk = dlg.exec_()
        if bOk:
            flags = (QTreeWidgetItemIterator.Checked | QTreeWidgetItemIterator.Enabled)
            treeIter = QTreeWidgetItemIterator(treeWdg, flags)
            sgShotIter = (it.value().data(0, Qt.UserRole) for it in treeIter)
            sgShotList = tuple(d for d in sgShotIter if d)
            if sgShotList:
                return bOk, sgShotList
        else:
            return bOk, tuple()

def initProject(sProjName=""):

    sProject = os.environ["DAVOS_INIT_PROJECT"] if not sProjName else sProjName
    proj = DamProject(sProject)
#    print sProject.center(80, "-")

    return proj

def genShotNames(iSeq, *shotNums):
    for n in shotNums:
        yield "sq{:04d}_sh{:04d}a".format(iSeq, n)
