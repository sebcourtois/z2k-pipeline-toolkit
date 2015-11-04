# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\modelpanelwidget.py
"""
# Released subject to the BSD License
# Please visit http://www.voidspace.org.uk/python/license.shtml
#
# Copyright (c) 2014, Kurt Rathjen
# All rights reserved.
# Comments, suggestions and bug reports are welcome.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
   # * Redistributions of source code must retain the above copyright
   #   notice, this list of conditions and the following disclaimer.
   # * Redistributions in binary form must reproduce the above copyright
   # notice, this list of conditions and the following disclaimer in the
   # documentation and/or other materials provided with the distribution.
   # * Neither the name of Kurt Rathjen nor the
   # names of its contributors may be used to endorse or promote products
   # derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY KURT RATHJEN ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL KURT RATHJEN BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
try:
    import shiboken
except Exception as e:
    import traceback
    traceback.print_exc()

from PySide import QtGui
from PySide import QtCore
try:
    import maya.cmds
    import maya.OpenMayaUI as mui
except Exception as e:
    import traceback
    print traceback.format_exc()

__all__ = ['SnapshotWindow', 'ModelPanelWidget', 'showSnapshotWindow']

class Window:
    main = None


def wrapinstance(ptr, base = None):
    """
    """
    if ptr is None:
        return
    else:
        ptr = long(ptr)
        qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
        metaObj = qObj.metaObject()
        cls = metaObj.className()
        superCls = metaObj.superClass().className()
        if hasattr(QtGui, cls):
            base = getattr(QtGui, cls)
        elif hasattr(QtGui, superCls):
            base = getattr(QtGui, superCls)
        else:
            base = QtGui.QWidget
        return shiboken.wrapInstance(long(ptr), base)


def unwrapinstance(qobject):
    """
    """
    return long(shiboken.getCppPointer(qobject)[0])


class ModelPanelWidget(QtGui.QWidget):

    def __init__(self, parent, name = 'customModelPanel', **kwargs):
        super(ModelPanelWidget, self).__init__(parent, **kwargs)
        try:
            maya.cmds.deleteUI('modelPanelWidget', panel=True)
        except:
            pass

        self.setObjectName('modelPanelWidget')
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName('modelPanelLayout')
        layout = mui.MQtUtil.fullName(unwrapinstance(self.verticalLayout))
        maya.cmds.setParent(layout)
        modelPanel = maya.cmds.modelPanel(name, label='ModelPanel')
        maya.cmds.modelEditor(modelPanel, edit=True, allObjects=False)
        maya.cmds.modelEditor(modelPanel, edit=True, grid=False)
        maya.cmds.modelEditor(modelPanel, edit=True, dynamics=False)
        maya.cmds.modelEditor(modelPanel, edit=True, activeOnly=False)
        maya.cmds.modelEditor(modelPanel, edit=True, manipulators=False)
        maya.cmds.modelEditor(modelPanel, edit=True, headsUpDisplay=False)
        maya.cmds.modelEditor(modelPanel, edit=True, selectionHiliteDisplay=False)
        maya.cmds.modelEditor(modelPanel, edit=True, polymeshes=True)
        maya.cmds.modelEditor(modelPanel, edit=True, nurbsSurfaces=True)
        maya.cmds.modelEditor(modelPanel, edit=True, subdivSurfaces=True)
        maya.cmds.modelEditor(modelPanel, edit=True, displayTextures=True)
        maya.cmds.modelEditor(modelPanel, edit=True, displayAppearance='smoothShaded')
        displayLights = maya.cmds.modelEditor(modelPanel, query=True, displayLights=True)
        maya.cmds.modelEditor(modelPanel, edit=True, displayLights=displayLights)
        self._modelPanel = modelPanel
        self.hideMenuBar()
        self.hideBarLayout()
        self.verticalLayout.addWidget(self.modelPanel())
        self.verticalLayout.itemAt(0).widget().hide()

    def name(self):
        return self._modelPanel

    def modelPanel(self):
        ptr = mui.MQtUtil.findControl(self._modelPanel)
        return wrapinstance(ptr, QtCore.QObject)

    def barLayout(self):
        name = maya.cmds.modelPanel(self._modelPanel, query=True, barLayout=True)
        ptr = mui.MQtUtil.findControl(name)
        return wrapinstance(ptr, QtCore.QObject)

    def hideBarLayout(self):
        self.barLayout().hide()

    def hideMenuBar(self):
        maya.cmds.modelPanel(self._modelPanel, edit=True, menuBarVisible=False)

    def setCamera(self, name):
        maya.cmds.modelPanel(self._modelPanel, edit=True, cam=name)

    def showEvent(self, event):
        super(ModelPanelWidget, self).showEvent(event)
        self.modelPanel().repaint()


class ModelPanelWindow(QtGui.QDialog):

    def __init__(self, parent, **kwargs):
        super(ModelPanelWindow, self).__init__(parent, **kwargs)
        self._width = 250
        self._height = 250
        self.setObjectName('modelPanelWindow')
        self.setWindowTitle('Qt Model Panel Window')
        self._label = QtGui.QLabel('x', self)
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName('modelPanelWindowLayout')
        self._modelPanel = ModelPanelWidget(self, 'modelPanelWidget')
        self.verticalLayout.addWidget(self.modelPanel())
        self.verticalLayout.addWidget(self.label())
        self.resize(self.width(), self.height())
        self.modelPanel().show()
        self.label().hide()

    def width(self):
        return self._width

    def height(self):
        return self._height

    def label(self):
        return self._label

    def modelPanel(self):
        return self._modelPanel

    def keyReleaseEvent(self, event):
        path = '/tmp/snapshot.png'
        modelPanel = 'modelPanelWidget'


class SnapshotWindow(QtGui.QDialog):

    def __init__(self, parent, **kwargs):
        QtGui.QDialogger.__init__(self, parent, **kwargs)
        self._width = 250
        self._height = 250
        try:
            maya.cmds.deleteUI('snapshotWindow', window=True)
        except:
            pass

        self.setObjectName('snapshotWindow')
        self.setWindowTitle('Snapshot Window')
        self._label = QtGui.QLabel('x', self)
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName('modelPanelWindowLayout')
        self._modelPanel = ModelPanelWidget(self, 'modelPanelWidget')
        self.verticalLayout.addWidget(self.modelPanel())
        self.verticalLayout.addWidget(self.label())
        self.resize(self.width(), self.height())
        self.modelPanel().show()
        self.label().hide()

    def width(self):
        return self._width

    def height(self):
        return self._height

    def label(self):
        return self._label

    def modelPanel(self):
        return self._modelPanel

    def keyReleaseEvent(self, event):
        path = '/tmp/snapshot.png'
        modelPanel = 'modelPanelWidget'


def showSnapshotWindow():
    if Window.main:
        return Window.main
    ptr = mui.MQtUtil.mainWindow()
    win = wrapinstance(ptr, QtCore.QObject)
    Window.main = SnapshotWindow(win)
    Window.main.show()
    return Window.main


def delete():
    try:
        maya.cmds.deleteUI('snapshotWindow', panel=True)
        maya.cmds.deleteUI('modelPanelWindow', window=True)
    except:
        pass

    Window.main = None
    return


if __name__ == '__main__':
    delete()
    show()