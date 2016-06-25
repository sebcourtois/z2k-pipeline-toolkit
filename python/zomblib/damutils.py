
import sys
import os
from collections import OrderedDict

from PySide import QtGui
from PySide.QtGui import QTreeWidgetItemIterator
from PySide.QtCore import Qt

#from pytd.util.qtutils import setWaitCursor
from pytd.util.fsutils import pathJoin
from pytd.util.sysutils import  qtGuiApp, inDevMode
from pytd.gui.dialogs import QuickTreeDialog

from davos.core.damproject import DamProject

def getShotDuration(sgShot):

    sShotCode = sgShot["code"]
    inOutDuration = sgShot['sg_cut_out'] - sgShot['sg_cut_in'] + 1
    duration = sgShot['sg_cut_duration']

    if inOutDuration != duration:
        print ("<{}> (sg_cut_out - sg_cut_in) = {} but sg_cut_duration = {}"
               .format(sShotCode, inOutDuration, duration))
    if duration < 1:
        raise ValueError("<{}> Invalid shot duration: {}.".format(sShotCode, duration))

    return duration

def playbackTimesFromDuration(duration, start=101):
    return dict(minTime=start, animationStartTime=start,
                maxTime=start + duration - 1, animationEndTime=start + duration - 1)

def playbackTimesFromShot(sgShot):
    return playbackTimesFromDuration(getShotDuration(sgShot))

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

def exportAssetTypePerShotCsv(proj):

    filters = [["asset.Asset.code", "starts_with", "fxp_"], ]
    astShotConnList = proj._shotgundb.sg.find("AssetShotConnection", filters, ["shot.Shot.code", "asset.Asset.code"])

    fxpPerShots = OrderedDict()
    for sgConn in astShotConnList:
        #pprint(sgConn)
        fxpPerShots.setdefault(sgConn["shot.Shot.code"], []).append(sgConn["asset.Asset.code"])

    import csv

    with open(r"C:\Users\sebcourtois\Downloads\fxpPerShots.csv", "wb") as csvFile:
        writer = csv.writer(csvFile, delimiter="|")
        for k, v in fxpPerShots.iteritems():
            print k, v
            writer.writerow((k, "\r\n".join(v)))

def initProject(sProjName=""):

    sProject = os.environ["DAVOS_INIT_PROJECT"] if not sProjName else sProjName
    proj = DamProject(sProject)
#    print sProject.center(80, "-")

    return proj

def genShotNames(iSeq, *shotNums):
    for n in shotNums:
        yield "sq{:04d}_sh{:04d}a".format(iSeq, n)
