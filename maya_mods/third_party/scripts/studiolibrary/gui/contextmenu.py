# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.13.0/build27/studiolibrary\gui\contextmenu.py
from PySide import QtGui
__all__ = ['ContextMenu']

class ContextMenu(QtGui.QMenu):

    def __init__(self, *args):
        QtGui.QMenu.__init__(self, *args)
        self._menus = []
        self._actions = []

    def actions(self):
        return self._actions

    def insertAction(self, actionBefore, action):
        if str(action.text()) not in self._actions:
            self._actions.append(str(action.text()))
            QtGui.QMenu.insertAction(self, actionBefore, action)

    def addAction(self, action):
        if str(action.text()) not in self._actions:
            self._actions.append(str(action.text()))
            QtGui.QMenu.addAction(self, action)

    def addMenu(self, menu):
        if str(menu.title()) not in self._menus:
            self._menus.append(str(menu.title()))
            QtGui.QMenu.addMenu(self, menu)