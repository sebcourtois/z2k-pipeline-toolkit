

from PySide import QtGui, QtCore

import maya.cmds as mc
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import pymel.core as pm

from pytd.util.sysutils import qtGuiApp
from dminutes.geocaching import meshMismatchStr

MSG = """
Select 3 vertices of the SAME FACE on the source mesh,
 
and then, IN THE SAME ORDER, the corresponding 3 vertices on the target mesh. 
"""

class TransferMeshDescDialog(MayaQWidgetBaseMixin, QtGui.QDialog):

    def __init__(self, *args, **kwargs):
        super(TransferMeshDescDialog, self).__init__(*args, **kwargs)

        self.setObjectName("TransferMeshDescDialog")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowTitle("Transfer Mesh Description")

        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(QtGui.QLabel(MSG, self))

        buttonBox = QtGui.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Horizontal)
        buttonBox.setObjectName("buttonBox")

        btn = buttonBox.addButton("Transfer", QtGui.QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.accept)
        btn = buttonBox.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        btn.clicked.connect(self.reject)

        layout.addWidget(buttonBox)

        self.savedSelection = mc.ls(sl=True)
        mc.select(clear=True)

        self.trackState = mc.selectPref(q=True, trackSelectionOrder=False)
        mc.selectPref(trackSelectionOrder=True)

    def done(self, accepted):

        if accepted:
            try:
                sSelList = mc.ls(os=True, flatten=True)

                if len(sSelList) != 6:
                    raise RuntimeError(MSG)

                sSrcMesh = sSelList[0].rsplit(".", 1)[0]
                sDstMesh = sSelList[3].rsplit(".", 1)[0]

                srcMeshStat = mc.polyEvaluate(sSrcMesh, v=True, f=True, e=True, t=True)
                dstMeshStat = mc.polyEvaluate(sDstMesh, v=True, f=True, e=True, t=True)

                if srcMeshStat != dstMeshStat:
                    sMsg = "Topology differs:"
                    sMsg += ("\n    - source mesh: {}  ('{}')"
                             .format(meshMismatchStr(srcMeshStat, dstMeshStat), sSrcMesh))
                    sMsg += ("\n    - target mesh: {}  ('{}')"
                             .format(meshMismatchStr(dstMeshStat, srcMeshStat), sDstMesh))
                    raise RuntimeError(sMsg)

                mc.meshRemap(*sSelList)

            except RuntimeError as e:
                pm.displayError(e.message.strip())
                return

            pm.displayWarning("Mesh description transfered !")

        mc.selectPref(trackSelectionOrder=self.trackState)

        if (not accepted) and self.savedSelection:
            try:
                mc.select(self.savedSelection)
            except Exception as e:
                pm.displayWarning(e.message.strip())

        return super(TransferMeshDescDialog, self).done(accepted)

def launch():
    dlg = None
    app = qtGuiApp()
    for w in app.topLevelWidgets():
        if w.objectName() == "TransferMeshDescDialog":
            dlg = w
    if dlg:
        dlg.showNormal()
        dlg.raise_()
        return

    mc.loadPlugin("meshReorder.mll", quiet=True)

    dlg = TransferMeshDescDialog()
    dlg.show()

launch()

