# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\gui\__init__.py
"""
Released subject to the BSD License
Please visit http://www.voidspace.org.uk/python/license.shtml

Contact: kurt.rathjen@gmail.com
Comments, suggestions and bug reports are welcome.
Copyright (c) 2015, Kurt Rathjen, All rights reserved.

It is a very non-restrictive license but it comes with the usual disclaimer.
This is free software: test it, break it, just don't blame me if it eats your
data! Of course if it does, let me know and I'll fix the problem so that it
doesn't happen to anyone else.

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
import os
import studiolibrary
from statuswidget import *
from folderswidget import *
from recordswidget import *
from librarywidget import *
from settingsdialog import *
from newfolderdialog import *
from tracebackwidget import *
from PySide import QtGui
from PySide import QtCore

class LibrarySettings(studiolibrary.MetaFile):

    def __init__(self, path):
        studiolibrary.MetaFile.__init__(self, path)
        self.setdefault('sort', studiolibrary.SortOption.Ordered)
        self.setdefault('showMenu', True)
        self.setdefault('showStatus', True)
        self.setdefault('showStatus', True)
        self.setdefault('showLabels', True)
        self.setdefault('showFolders', True)
        self.setdefault('showPreview', True)
        self.setdefault('showDeleted', False)
        self.setdefault('showStatusDialog', True)
        self.setdefault('spacing', 1)
        self.setdefault('dockArea', None)
        self.setdefault('tabletMode', False)
        self.setdefault('filter', '')
        self.setdefault('iconSize', 100)
        self.setdefault('foldersState', {})
        self.setdefault('selectedRecords', [])
        self.setdefault('sizes', [120, 280, 160])
        self.setdefault('geometry', [100,
         100,
         640,
         560])
        return


class PreviewFrame(QtGui.QWidget):

    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)


class PreviewWidget(QtGui.QWidget):

    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        studiolibrary.loadUi(self)

    def window(self):
        return self.parent().window()


class FoldersFrame(QtGui.QFrame):

    def __init__(self, *args):
        QtGui.QFrame.__init__(self, *args)
        studiolibrary.loadUi(self)

    def window(self):
        return self.parent().window()


class InfoFrame(QtGui.QMainWindow):

    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent, QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        studiolibrary.loadUi(self)

    def _show(self, rect):
        QtGui.QMainWindow.show(self)


class CheckForUpdatesThread(QtCore.QThread):

    def __init__(self, *args):
        QtCore.QThread.__init__(self, *args)

    def run(self):
        if studiolibrary.package().isUpdateAvailable():
            self.emit(QtCore.SIGNAL('updateAvailable()'))


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