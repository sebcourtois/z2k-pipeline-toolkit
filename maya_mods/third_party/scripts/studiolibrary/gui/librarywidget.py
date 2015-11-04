# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\gui\librarywidget.py
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
import time
import logging
import studiolibrary
from PySide import QtGui
from PySide import QtCore
__all__ = ['LibraryWidget']
logger = logging.getLogger(__name__)

class LibraryWidget(QtGui.QWidget):

    @staticmethod
    def generateUniqueObjectName(name):
        """
        @type name: str
        :rtype: str
        """
        names = [ w.objectName() for w in studiolibrary.Library.windows() ]
        return studiolibrary.generateUniqueName(name, names)

    def setUniqueObjectName(self, name):
        """
        @type name: str
        :rtype: None
        """
        uniqueName = self.generateUniqueObjectName(name)
        self.setObjectName(uniqueName)

    def __init__(self, library):
        """
        @type library: studiolibrary.Library
        """
        QtGui.QWidget.__init__(self, None)
        studiolibrary.loadUi(self)
        logger.info("Loading library window '%s'" % library.name())
        self._library = library
        self.setUniqueObjectName('studiolibrary')
        studiolibrary.analytics().logScreen('MainWindow')
        self._libraryActions = []
        self._pSize = None
        self._pShow = None
        self._dockArea = None
        self._isLocked = False
        self._isLoaded = False
        self._showFolders = False
        self._updateThread = None
        self._previewRecord = None
        self._showLabelsAction = True
        self._saveSettingsOnClose = True
        self._sort = studiolibrary.SortOption.Ordered
        self._mayaDockWidget = None
        self._mayaLayoutWidget = None
        self.ui.dialogWidget = None
        self.ui.createWidget = None
        self.ui.previewWidget = None
        self.ui.infoFrame = studiolibrary.InfoFrame(self)
        self.ui.statusWidget = studiolibrary.StatusWidget(self)
        self.ui.foldersWidget = studiolibrary.FoldersWidget(self)
        self.ui.previewFrame = studiolibrary.PreviewFrame(self)
        self.ui.recordsWidget = studiolibrary.RecordsWidget(self)
        self.connect(self.ui.updateButton, QtCore.SIGNAL('clicked()'), self.help)
        self.connect(self.ui.createButton, QtCore.SIGNAL('clicked()'), self.showNewMenu)
        self.connect(self.ui.settingsButton, QtCore.SIGNAL('clicked()'), self.showSettingsMenu)
        pixmap = studiolibrary.icon('cog', QtGui.QColor(255, 255, 255, 220), ignoreOverride=True)
        self.ui.settingsButton.setIcon(pixmap)
        pixmap = studiolibrary.icon('addItem', QtGui.QColor(255, 255, 255, 240), ignoreOverride=True)
        self.ui.createButton.setIcon(pixmap)
        self.ui.updateButton.hide()
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.ui.splitter = QtGui.QSplitter(QtCore.Qt.Horizontal, self)
        self.ui.splitter.setHandleWidth(1)
        self.ui.splitter.setChildrenCollapsible(False)
        self.ui.viewLayout.insertWidget(1, self.ui.splitter)
        self.ui.splitter.insertWidget(0, self.ui.foldersWidget)
        self.ui.splitter.insertWidget(1, self.ui.recordsWidget)
        self._contextMenu = studiolibrary.ContextMenu
        vbox = QtGui.QVBoxLayout()
        self.ui.previewFrame.setLayout(vbox)
        self.ui.previewFrame.layout().setSpacing(0)
        self.ui.previewFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.ui.previewFrame.setMinimumWidth(5)
        self.ui.viewLayout.insertWidget(2, self.ui.previewFrame)
        self.ui.splitter.insertWidget(2, self.ui.previewFrame)
        self.ui.statusLayout.addWidget(self.ui.statusWidget)
        self.ui.newMenu = QtGui.QMenu(self)
        self.ui.newMenu.setTitle('New')
        self.ui.newMenu.setIcon(studiolibrary.icon('new14'))
        action = QtGui.QAction(studiolibrary.icon('folder14'), 'Folder', self.ui.newMenu)
        self.connect(action, QtCore.SIGNAL('triggered(bool)'), self.showCreateFolderDialog)
        self.ui.newMenu.addAction(action)
        action = QtGui.QAction(studiolibrary.icon('addLibrary13', QtGui.QColor(255, 255, 255, 200)), 'Library', self.ui.newMenu)
        self.connect(action, QtCore.SIGNAL('triggered(bool)'), self.showNewLibraryDialog)
        self.ui.newMenu.addAction(action)
        separator = QtGui.QAction('', self.ui.newMenu)
        separator.setSeparator(True)
        self.ui.newMenu.addAction(separator)
        self.ui.editRecordMenu = studiolibrary.ContextMenu(self)
        self.ui.editRecordMenu.setTitle('Edit')
        self.ui.printPrettyAction = QtGui.QAction(studiolibrary.icon('print'), 'Print', self.ui.editRecordMenu)
        action.connect(self.ui.printPrettyAction, QtCore.SIGNAL('triggered(bool)'), self.printPrettyRecords)
        self.ui.editRecordMenu.addAction(self.ui.printPrettyAction)
        self.ui.deleteRecordAction = QtGui.QAction(studiolibrary.icon('trash'), 'Delete', self.ui.editRecordMenu)
        action.connect(self.ui.deleteRecordAction, QtCore.SIGNAL('triggered(bool)'), self.deleteSelectedRecords)
        self.ui.editRecordMenu.addAction(self.ui.deleteRecordAction)
        self.ui.deleteRenameAction = QtGui.QAction(studiolibrary.icon('rename'), 'Rename', self.ui.editRecordMenu)
        action.connect(self.ui.deleteRenameAction, QtCore.SIGNAL('triggered(bool)'), self.renameSelectedRecord)
        self.ui.editRecordMenu.addAction(self.ui.deleteRenameAction)
        self.ui.showRecordAction = QtGui.QAction(studiolibrary.icon('folder14'), 'Show in folder', self.ui.editRecordMenu)
        action.connect(self.ui.showRecordAction, QtCore.SIGNAL('triggered(bool)'), self.openSelectedRecords)
        self.ui.editRecordMenu.addAction(self.ui.showRecordAction)
        self.ui.editFolderMenu = studiolibrary.ContextMenu(self)
        self.ui.editFolderMenu.setTitle('Edit')
        action = QtGui.QAction(studiolibrary.icon('trash'), 'Delete', self.ui.editFolderMenu)
        action.connect(action, QtCore.SIGNAL('triggered(bool)'), self.deleteSelectedFolders)
        self.ui.editFolderMenu.addAction(action)
        action = QtGui.QAction(studiolibrary.icon('rename'), 'Rename', self.ui.editFolderMenu)
        action.connect(action, QtCore.SIGNAL('triggered(bool)'), self.renameSelectedFolder)
        self.ui.editFolderMenu.addAction(action)
        action = QtGui.QAction(studiolibrary.icon('folder14'), 'Show in folder', self.ui.editFolderMenu)
        action.connect(action, QtCore.SIGNAL('triggered(bool)'), self.openSelectedFolders)
        self.ui.editFolderMenu.addAction(action)
        self.ui.sortMenu = QtGui.QMenu(self)
        self.ui.sortMenu.setTitle('Sort by')
        self._sortNameAction = QtGui.QAction('Name', self.ui.sortMenu)
        self._sortNameAction.setCheckable(True)
        self.connect(self._sortNameAction, QtCore.SIGNAL('triggered(bool)'), self.setSortName)
        self.ui.sortMenu.addAction(self._sortNameAction)
        self._sortModifiedAction = QtGui.QAction('Modified', self.ui.sortMenu)
        self._sortModifiedAction.setCheckable(True)
        self.connect(self._sortModifiedAction, QtCore.SIGNAL('triggered(bool)'), self.setSortModified)
        self.ui.sortMenu.addAction(self._sortModifiedAction)
        self._sortOrderedAction = QtGui.QAction('Ordered', self.ui.sortMenu)
        self._sortOrderedAction.setCheckable(True)
        self.connect(self._sortOrderedAction, QtCore.SIGNAL('triggered(bool)'), self.setSortOrdered)
        self.ui.sortMenu.addAction(self._sortOrderedAction)
        self.ui.settingsMenu = QtGui.QMenu(self)
        self.ui.settingsMenu.setIcon(studiolibrary.icon('settings14'))
        self.ui.settingsMenu.setTitle('Settings')
        self._librariesMenu = studiolibrary.LibrariesMenu(self.ui.settingsMenu)
        self._librariesMenu.setTitle('Libraries')
        self.ui.settingsMenu.addMenu(self._librariesMenu)
        self.ui.settingsMenu.addSeparator()
        self._showSettingsAction = QtGui.QAction('Settings', self.ui.settingsMenu)
        self.connect(self._showSettingsAction, QtCore.SIGNAL('triggered(bool)'), self.showSettings)
        self.ui.settingsMenu.addAction(self._showSettingsAction)
        separator = QtGui.QAction('', self.ui.settingsMenu)
        separator.setSeparator(True)
        self.ui.settingsMenu.addAction(separator)
        self._showMenuAction = QtGui.QAction('Show menu', self.ui.settingsMenu)
        self._showMenuAction.setCheckable(True)
        self.connect(self._showMenuAction, QtCore.SIGNAL('triggered(bool)'), self.showMenu)
        self.ui.settingsMenu.addAction(self._showMenuAction)
        self._showFoldersAction = QtGui.QAction('Show folders', self.ui.settingsMenu)
        self._showFoldersAction.setCheckable(True)
        self.connect(self._showFoldersAction, QtCore.SIGNAL('triggered(bool)'), self.showFolders)
        self.ui.settingsMenu.addAction(self._showFoldersAction)
        self._showPreviewAction = QtGui.QAction('Show preview', self.ui.settingsMenu)
        self._showPreviewAction.setCheckable(True)
        self.connect(self._showPreviewAction, QtCore.SIGNAL('triggered(bool)'), self.showPreview)
        self.ui.settingsMenu.addAction(self._showPreviewAction)
        self._showStatusAction = QtGui.QAction('Show status', self.ui.settingsMenu)
        self._showStatusAction.setCheckable(True)
        self.connect(self._showStatusAction, QtCore.SIGNAL('triggered(bool)'), self.showStatus)
        self.ui.settingsMenu.addAction(self._showStatusAction)
        self._showStatusDialogAction = QtGui.QAction('Show dialogs', self.ui.settingsMenu)
        self._showStatusDialogAction.setCheckable(True)
        self.connect(self._showStatusDialogAction, QtCore.SIGNAL('triggered(bool)'), self.showStatusDialog)
        self.ui.settingsMenu.addAction(self._showStatusDialogAction)
        self.ui.settingsMenu.addSeparator()
        self._showLabelsAction = QtGui.QAction('Show labels', self.ui.settingsMenu)
        self._showLabelsAction.setCheckable(True)
        self.connect(self._showLabelsAction, QtCore.SIGNAL('triggered(bool)'), self.showLabels)
        self.ui.settingsMenu.addAction(self._showLabelsAction)
        if studiolibrary.isMaya():
            self.ui.settingsMenu.addSeparator()
            self._dockLeftAction = QtGui.QAction('Dock left', self.ui.settingsMenu)
            self.connect(self._dockLeftAction, QtCore.SIGNAL('triggered(bool)'), self.dockLeft)
            self.ui.settingsMenu.addAction(self._dockLeftAction)
            self._dockRightAction = QtGui.QAction('Dock right', self.ui.settingsMenu)
            self.connect(self._dockRightAction, QtCore.SIGNAL('triggered(bool)'), self.dockRight)
            self.ui.settingsMenu.addAction(self._dockRightAction)
        self.ui.settingsMenu.addSeparator()
        self._setDebugAction = QtGui.QAction('Debug mode', self.ui.settingsMenu)
        self._setDebugAction.setCheckable(True)
        self._setDebugAction.setChecked(False)
        self.connect(self._setDebugAction, QtCore.SIGNAL('triggered(bool)'), self.setDebugMode)
        self.ui.settingsMenu.addAction(self._setDebugAction)
        self._helpAction = QtGui.QAction('Help', self.ui.settingsMenu)
        self.connect(self._helpAction, QtCore.SIGNAL('triggered(bool)'), self.help)
        self.ui.settingsMenu.addAction(self._helpAction)
        self.checkForUpdates()
        self.setLibrary(library)
        self.foldersWidget().onDropped.connect(self.onRecordDropped)
        self.foldersWidget().onSelectionChanged.connect(self.folderSelectionChanged)
        self.foldersWidget().onShowContextMenu.connect(self.onShowFolderContextMenu)
        self.recordsWidget().onDropped.connect(self.onRecordDropped)
        self.recordsWidget().onOrderChanged.connect(self.onRecordOrderChanged)
        self.recordsWidget().onShowContextMenu.connect(self.onShowRecordContextMenu)
        self.recordsWidget().onSelectionChanged.connect(self.onRecordSelectionChanged)
        studiolibrary.Record.onSaved.connect(self.onRecordSaved)
        studiolibrary.SettingsDialog.onColorChanged.connect(self.onSettingsColorChanged)
        studiolibrary.SettingsDialog.onBackgroundColorChanged.connect(self.onSettingsBackgroundColorChanged)
        return

    def onShowFolderContextMenu(self, menu):
        """
        :type menu: QtGui.QMenu
        :rtype: None
        """
        folders = self.selectedFolders()
        if self.isLocked():
            return
        menu.addMenu(self.ui.newMenu)
        if len(folders) == 1:
            menu.addMenu(self.ui.editFolderMenu)
        if not folders:
            menu.addSeparator()
            menu.addMenu(self.ui.settingsMenu)

    def onShowRecordContextMenu(self):
        """
        :rtype: return
        """
        menu = self.contextMenu(self)
        records = self.recordsWidget().selectedRecords()
        for plugin in self.plugins().values():
            plugin.recordContextMenu(menu, records)

        if not self.isLocked():
            menu.addMenu(self.ui.newMenu)
            menu.addMenu(self.ui.editRecordMenu)
        menu.addSeparator()
        menu.addMenu(self.ui.sortMenu)
        menu.addMenu(self.ui.settingsMenu)
        point = QtGui.QCursor.pos()
        point.setX(point.x() + 3)
        point.setY(point.y() + 3)
        menu.exec_(point)
        menu.close()

    def folderSelectionChanged(self, selectedFolders, deselectedFolders):
        for plugin in self.plugins().values():
            plugin.folderSelectionChanged(selectedFolders, deselectedFolders)

        self.reloadRecords()

    def onRecordOrderChanged(self):
        """
        :rtype: None
        """
        folders = self.selectedFolders()
        if len(folders) == 1:
            folder, = folders
            order = []
            for record in self.recordsWidget().model().records():
                order.append(record.name())

            folder.setOrder(order)

    def onRecordDropped(self, event):
        """
        :type event: list[studiolibrary.Record]
        :rtype: None
        """
        mimeData = event.mimeData()
        if hasattr(mimeData, 'records'):
            records = mimeData.records()
            folder = self.selectedFolder()
            self.moveRecordsToFolder(records, folder)

    def moveRecordsToFolder(self, records, folder):
        """
        :type records: list[studiolibrary.Record]
        :type folder: studiolibrary.Folder
        :rtype: None
        """
        try:
            for record in records:
                path = folder.path() + '/' + record.name()
                record.rename(path)

        except Exception as msg:
            self.setError(msg)
        finally:
            self.reloadRecords()
            self.selectRecords(records)

    def onRecordSelectionChanged(self, selectedRecords = None, deselectedRecords = None):
        """
        :type selectedRecords: list[studiolibrary.Record]
        :type deselectedRecords: list[studiolibrary.Record]
        :return:
        """
        record = self.recordsWidget().selectedRecord()
        if record:
            record.plugin().showPreviewWidget(self, record)
        else:
            self.clearPreviewWidget()

    def onRecordSaved(self, record):
        """
        :type record: studiolibrary.Record
        :rtype: None
        """
        folder = self.selectedFolder()
        if folder and folder.path() == record.dirname():
            self.reloadRecords()
            self.selectRecords([record])

    def onSettingsColorChanged(self, settingsWindow):
        """
        :type settingsWindow: studiolibrary.SettingsWindow
        :rtype: None
        """
        if self.library() == settingsWindow.library():
            self.library().setColor(settingsWindow.color())
            self.reloadStyleSheet()

    def onSettingsBackgroundColorChanged(self, settingsWindow):
        """
        :type settingsWindow: studiolibrary.SettingsWindow
        :rtype: None
        """
        if self.library() == settingsWindow.library():
            self.library().setBackgroundColor(settingsWindow.backgroundColor())
            self.reloadStyleSheet()

    def showNewLibraryDialog(self):
        """
        :rtype: None
        """
        studiolibrary.Library.showNewLibraryDialog()

    def recordsWidget(self):
        """
        :rtype: studiolibrary.RecordsWidget
        """
        return self.ui.recordsWidget

    def foldersWidget(self):
        """
        :rtype: studiolibrary.FoldersWidget
        """
        return self.ui.foldersWidget

    def previewWidget(self):
        """
        :rtype: studiolibrary.QWidget
        """
        return self.ui.previewWidget

    def isListView(self):
        """
        @type: bool
        """
        return self.ui.recordsWidget.viewMode() == QtGui.QListView.ListMode

    def isIconView(self):
        """
        :type: bool
        """
        return self.ui.recordsWidget.viewMode() == QtGui.QListView.IconMode

    def checkForUpdates(self):
        """
        :rtype: None
        """
        if studiolibrary.CHECK_FOR_UPDATES_ENABLED:
            if not self._updateThread:
                self._updateThread = studiolibrary.CheckForUpdatesThread(self)
                self.connect(self._updateThread, QtCore.SIGNAL('updateAvailable()'), self.setUpdateAvailable)
            self._updateThread.start()
        else:
            logger.debug('Check for updates has been disabled!')

    def resetSettings(self):
        """
        :rtype: None
        """
        try:
            s = studiolibrary.LibrarySettings('None')
            settings = self.settings()
            settings.data().update(s)
            settings.save()
            self.loadSettings()
            self.clearSelection()
        except Exception as e:
            import traceback
            traceback.print_exc()

    def setLibrary(self, library):
        """
        :type library: studiolibrary.Library
        """
        self._library = library
        self.reloadLibrary()

    def reloadLibrary(self):
        """
        :rtype: None
        """
        self.clearRecords()
        self.clearPreviewWidget()
        self.setFolderPath(self.library().path())
        self.updateWindowTitle()
        self.updateSettingsMenu()

    def setFolderPath(self, path):
        """
        :type path: str
        :rtype: None
        """
        self.ui.foldersWidget.clearSelection()
        self.ui.foldersWidget.setRootPath(path)

    def library(self):
        """
        :rtype: studiolibrary.Library
        """
        return self._library

    def showSettings(self):
        """
        """
        library = self.library()
        name = library.name()
        location = library.path()
        result = library.execSettingsDialog()
        if result == QtGui.QDialog.Accepted:
            self.saveSettings()
            if location != library.path():
                self.reloadLibrary()
            if name != library.name():
                self.updateWindowTitle()
        self.reloadStyleSheet()

    def setUpdateAvailable(self):
        self.ui.updateButton.show()

    def warningDialog(self, message, title = 'Warning'):
        return QtGui.QMessageBox.warning(self, title, str(message))

    def criticalDialog(self, message, title = 'Error'):
        return QtGui.QMessageBox.critical(self, title, str(message))

    def informationDialog(self, message, title = 'Information'):
        return QtGui.QMessageBox.information(self, title, str(message))

    def questionDialog(self, message, title = 'Question'):
        return QtGui.QMessageBox.question(self, title, str(message), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)

    def setError(self, text, msec = 6000):
        text = str(text)
        self.ui.statusWidget.setError(text, msec=msec)
        if self.isShowStatusDialog():
            self.criticalDialog(text)
        else:
            self.showStatus(True)

    def setWarning(self, text, msec = 6000):
        text = str(text)
        self.ui.statusWidget.setWarning(text, msec=msec)
        if self.isShowStatusDialog():
            self.warningDialog(text)
        else:
            self.showStatus(True)

    def isShowStatusDialog(self):
        return self._showStatusDialogAction.isChecked()

    def showStatusDialog(self, v):
        self._showStatusDialogAction.setChecked(v)

    def setInfo(self, text, msec = 6000):
        self.ui.statusWidget.setInfo(text, msec=msec)

    def event(self, event):
        if isinstance(event, QtGui.QStatusTipEvent):
            self.ui.statusWidget.setInfo(event.tip())
        return QtGui.QWidget.event(self, event)

    def updateWindowTitle(self):
        if self.isDocked():
            title = 'Studio Library - ' + self.name()
        else:
            title = 'Studio Library - ' + studiolibrary.__version__ + ' - ' + self.name()
        if self.isLocked():
            title += ' (Locked)'
        self.setWindowTitle(title)
        if studiolibrary.isMaya() and self._mayaDockWidget:
            import maya.cmds
            maya.cmds.dockControl(self._mayaDockWidget, edit=True, label=title)

    def setLocked(self, value):
        self.foldersWidget().setLocked(value)
        self.recordsWidget().setLocked(value)
        if value:
            self.ui.createButton.setEnabled(True)
            self.ui.createButton.setIcon(studiolibrary.icon('lock', QtGui.QColor(255, 255, 255, 222), ignoreOverride=True))
        else:
            self.ui.createButton.setEnabled(True)
            self.ui.createButton.setIcon(studiolibrary.icon('addItem', ignoreOverride=True))
            self.ui.createButton.show()
        self._isLocked = value
        self.updateWindowTitle()

    def kwargs(self):
        """
        :rtype: dict[]
        """
        return self.library().kwargs()

    def isLocked(self):
        """
        :rtype: bool
        """
        return self._isLocked

    def setContextMenu(self, menu):
        """
        :type: QtGui.QMenu
        """
        self._contextMenu = menu

    def contextMenu(self, parent):
        """
        :rtype: QtGui.QMenu
        """
        return self._contextMenu(parent)

    def leaveEvent(self, event):
        pass

    def window(self):
        return self

    def isDocked(self):
        if studiolibrary.isMaya():
            import maya.cmds
            if self._mayaDockWidget:
                return not maya.cmds.dockControl(self._mayaDockWidget, query=True, floating=True)
        return False

    def dockArea(self):
        if not self.parent():
            return None
        else:
            return self._dockArea

    def destroy(self):
        """
        :rtype: None
        """
        self.close()
        self.library().unloadPlugins()
        self.library().setWindow(None)
        self.deleteDockWidget()
        return

    def dockLocationWindowChanged(self, area):
        if studiolibrary.isPySide():
            if area == QtCore.Qt.DockWidgetArea.RightDockWidgetArea:
                self._dockArea = 2
            elif area == QtCore.Qt.DockWidgetArea.LeftDockWidgetArea:
                self._dockArea = 1
        else:
            self._dockArea = area
        self.updateWindowTitle()
        self.parentX().setMinimumWidth(15)

    def topLevelWindowChanged(self, value, *args):
        if value:
            self._dockArea = None
        self.updateWindowTitle()
        self.parentX().setMinimumWidth(15)
        return

    def raiseWindow(self):
        if studiolibrary.isMaya() and self._mayaDockWidget:
            import maya.cmds
            maya.cmds.dockControl(self._mayaDockWidget, edit=True, visible=True, r=True)

    def dockLeft(self):
        self.setDockArea(1, self.width(), edit=True)

    def dockRight(self):
        self.setDockArea(2, self.width(), edit=True)

    def deleteDockWidget(self):
        if studiolibrary.isMaya():
            import maya.cmds
            if maya.cmds.dockControl(str(self._mayaDockWidget), q=1, ex=1):
                maya.cmds.deleteUI(str(self._mayaDockWidget))
                self._mayaDockWidget = None
            if maya.cmds.columnLayout(str(self._mayaLayoutWidget), q=1, ex=1):
                maya.cmds.deleteUI(str(self._mayaLayoutWidget))
                self._mayaLayoutWidget = None
        return

    def floating(self):
        if studiolibrary.isMaya():
            import maya.cmds
            if maya.cmds.dockControl(str(self.objectName()), q=1, ex=1):
                maya.cmds.dockControl(str(self.objectName()), e=1, fl=1)

    def setDockArea(self, dockArea = None, width = None, edit = False):
        self._dockArea = dockArea
        allowedAreas = ['right', 'left']
        if dockArea == 1:
            area = 'left'
            floating = False
        elif dockArea == 2:
            area = 'right'
            floating = False
        else:
            area = 'left'
            floating = True
        if studiolibrary.isMaya():
            import maya.cmds
            if not self._mayaDockWidget:
                self.deleteDockWidget()
                if not self._mayaLayoutWidget:
                    self._mayaLayoutWidget = maya.cmds.columnLayout(parent=str(self.objectName()))
                maya.cmds.layout(self._mayaLayoutWidget, edit=True, visible=False)
                self._mayaDockWidget = maya.cmds.dockControl(area=area, floating=False, r=True, content=str(self.objectName()), allowedArea=allowedAreas, width=15)
                if self.parent():
                    self.connect(self.parent(), QtCore.SIGNAL('topLevelChanged(bool)'), self.topLevelWindowChanged)
                    self.connect(self.parent(), QtCore.SIGNAL('dockLocationChanged(Qt::DockWidgetArea)'), self.dockLocationWindowChanged)
            self.updateWindowTitle()
            maya.cmds.dockControl(self._mayaDockWidget, edit=True, r=True, area=area, floating=floating, width=width)

    def isShowLabels(self):
        return self.ui.recordsWidget.isShowLabels()

    def reloadStyleSheet(self):
        styleSheet = self.library().styleSheet()
        theme = self.library().theme()
        color = studiolibrary.Color.fromString(theme['RECORD_TEXT_COLOR'])
        self.recordsWidget().setTextColor(color)
        color = studiolibrary.Color.fromString(theme['RECORD_TEXT_SELECTED_COLOR'])
        self.recordsWidget().setTextSelectedColor(color)
        color = studiolibrary.Color.fromString(theme['RECORD_BACKGROUND_COLOR'])
        self.recordsWidget().setBackgroundColor(color)
        color = studiolibrary.Color.fromString(theme['RECORD_BACKGROUND_SELECTED_COLOR'])
        self.recordsWidget().setBackgroundSelectedColor(color)
        self.setStyleSheet(styleSheet)

    def name(self):
        return self.library().name()

    def settings(self):
        return self.library().settings()

    def openSelectedFolders(self):
        folders = self.selectedFolders()
        for folder in folders:
            folder.openLocation()

    def openSelectedRecords(self):
        records = self.selectedRecords()
        for record in records:
            record.openLocation()

        if not records:
            for folder in self.selectedFolders():
                folder.openLocation()

    def renameSelectedRecord(self):
        """
        """
        try:
            self._renameSelectedRecord()
        except Exception as msg:
            self.criticalDialog(msg)
            raise

    def _renameSelectedRecord(self):
        """
        :rtype: None
        """
        record = self.recordsWidget().selectedRecord()
        if not record:
            raise Exception('Please select a record')
        result = record.showRenameDialog(parent=self)
        if result:
            self.reloadRecords()
            self.selectRecords([record])

    def renameSelectedFolder(self):
        """
        """
        try:
            self.ui.foldersWidget.showRenameDialog(parent=self)
        except Exception as msg:
            self.criticalDialog(msg)
            raise

    def printPrettyRecords(self):
        """
        """
        for r in self.ui.recordsWidget.selectedRecords():
            r.prettyPrint()

    def parentX(self):
        return self.parent() or self

    def loadSettings(self, ignoreWindowSettings = False):
        """
        :type ignoreWindowSettings: bool
        :rtype: None
        """
        settings = studiolibrary.LibrarySettings('None')
        librarySettings = self.settings().data()
        settings.data().update(librarySettings)
        try:
            self.showMenu(settings.get('showMenu'))
            self.showFolders(settings.get('showFolders'))
            self.showPreview(settings.get('showPreview'))
            self.showStatusDialog(settings.get('showStatusDialog'))
            self.showStatus(settings.get('showStatus'))
            self.showLabels(settings.get('showLabels'))
            self.setSort(settings.get('sort'), force=False)
            self.ui.recordsWidget.setViewSize(settings.get('iconSize'))
            self.reloadStyleSheet()
        except Exception as e:
            self.parentX().move(100, 100)
            self.setError('An error has occurred while loading settings! Please check the script editor for the traceback.')
            import traceback
            traceback.print_exc()

        self.loadPlugins()
        self.ui.foldersWidget.restoreState(settings.get('foldersState'))
        self.selectRecords(settings.get('selectedRecords'))
        try:
            fSize, cSize, pSize = settings.get('sizes')
            if pSize == 0:
                pSize = 200
            if fSize == 0:
                fSize = 120
            self.ui.splitter.setSizes([fSize, cSize, pSize])
            self.ui.splitter.setStretchFactor(1, 1)
            if not ignoreWindowSettings:
                x, y, width, height = settings.get('geometry')
                if width == 0:
                    width = fSize + cSize + pSize
                dockArea = settings.get('dockArea')
                self.setDockArea(dockArea, width=width)
                if not self.isDocked():
                    self.parentX().setGeometry(x, y, width, height)
                self.parentX().setMinimumWidth(15)
        except:
            self.parentX().move(100, 100)
            self.setError('An error has occurred while loading settings! Please check the script editor for the traceback.')
            import traceback
            traceback.print_exc()
            raise

    def saveSettings(self):
        """
        :rtype: None
        """
        if not self.isLoaded():
            return
        try:
            geometry = (self.parentX().geometry().x(),
             self.parentX().geometry().y(),
             self.parentX().geometry().width(),
             self.parentX().geometry().height())
            settings = self.settings()
            settings.set('showMenu', self._showMenuAction.isChecked())
            settings.set('showLabels', self._showLabelsAction.isChecked())
            settings.set('showStatus', self._showStatusAction.isChecked())
            settings.set('showFolders', self._showFoldersAction.isChecked())
            settings.set('showPreview', self._showPreviewAction.isChecked())
            settings.set('showStatusDialog', self._showStatusDialogAction.isChecked())
            settings.set('sort', self._sort)
            settings.set('geometry', geometry)
            settings.set('dockArea', self._dockArea)
            settings.set('sizes', self.ui.splitter.sizes())
            settings.set('foldersState', self.ui.foldersWidget.currentState())
            settings.set('selectedRecords', [ record.path() for record in self.selectedRecords() ])
            settings.set('iconSize', self.ui.recordsWidget.viewSize())
            settings.save()
        except:
            import traceback
            traceback.print_exc()

    def clearPreviewWidget(self):
        widget = studiolibrary.PreviewWidget(None)
        self.setPreviewWidget(widget)
        return

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F5:
            self.reloadFolders()
        QtGui.QWidget.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        for record in self.selectedRecords():
            record.keyReleaseEvent(event)

        QtGui.QWidget.keyReleaseEvent(self, event)

    def isLoaded(self):
        return self._isLoaded

    def showEvent(self, event):
        if not self._isLoaded:
            self.move(-50000, -50000)
        QtGui.QWidget.showEvent(self, event)
        try:
            if not self._isLoaded:
                self.loadSettings()
                self._isLoaded = True
        except:
            import traceback
            traceback.print_exc()

        if self._isLoaded:
            g = self.geometry()
            if g.x() < 0 or g.y() < 0:
                self.parentX().move(100, 100)

    def close(self, saveSettings = True):
        self._saveSettingsOnClose = saveSettings
        QtGui.QWidget.close(self)

    def closeEvent(self, event):
        if self.isLoaded() and self._saveSettingsOnClose:
            self.saveSettings()
        QtGui.QWidget.closeEvent(self, event)

    def showMessage(self, text, repaint = True):
        self.ui.recordsWidget.showMessage(text, repaint=repaint)

    def resizeEvent(self, event):
        QtGui.QWidget.resizeEvent(self, event)

    def updateLayout(self):
        pass

    def root(self):
        return self.library().path()

    def setCreateWidget(self, widget):
        if widget and not self._pSize:
            fSize, cSize, pSize = self.ui.splitter.sizes()
            self._pSize = pSize
            self._pShow = self.isShowPreview()
            self.ui.splitter.setSizes([fSize, cSize, widget.minimumWidth()])
        self.showPreview(True)
        self.ui.recordsWidget.clearSelection()
        self.setPreviewWidget(widget)

    def previewRecord(self):
        return self._previewRecord

    def setPreviewWidget(self, widget, record = None):
        if self.ui.previewWidget == widget:
            logger.debug("Preview widget already contains widget '%s'" % str(widget))
            return
        if self.ui.previewWidget:
            self.ui.previewWidget.close()
        for i in range(self.ui.previewFrame.layout().count()):
            widget2 = self.ui.previewFrame.layout().itemAt(i).widget()
            self.ui.previewFrame.layout().removeWidget(widget2)
            widget2.setParent(self)
            widget2.hide()
            widget2.close()
            widget2.destroy()
            del widget2

        self.ui.previewWidget = widget
        if self.isShowPreview():
            if self.ui.previewWidget:
                self.ui.previewFrame.layout().addWidget(self.ui.previewWidget)
                self.ui.previewWidget.show()
        self._previewRecord = record

    def selectRecords(self, records):
        self.ui.recordsWidget.selectRecords(records)

    def selectFolders(self, folders):
        self.ui.foldersWidget.selectFolders(folders)

    def clearSelection(self):
        self.ui.foldersWidget.clearSelection()

    def selectedRecords(self):
        return self.ui.recordsWidget.selectedRecords()

    def selectedFolder(self):
        """
        :rtype: studiolibrary.Folder
        """
        folders = self.selectedFolders()
        if folders:
            return folders[0]
        else:
            return None

    def selectedFolders(self):
        return self.ui.foldersWidget.selectedFolders()

    def setViewMode(self, mode):
        return self.ui.recordsWidget.setViewMode(mode)

    def viewMode(self):
        return self.ui.recordsWidget.viewMode()

    def sort(self):
        return self._sort

    def setSort(self, sort, force = True):
        self._sort = sort
        if sort == studiolibrary.SortOption.Ordered:
            self.ui.recordsWidget.setDropEnabled(True)
        else:
            self.ui.recordsWidget.setDropEnabled(False)
        self._sortNameAction.setChecked(studiolibrary.SortOption.Name == sort)
        self._sortOrderedAction.setChecked(studiolibrary.SortOption.Ordered == sort)
        self._sortModifiedAction.setChecked(studiolibrary.SortOption.Modified == sort)
        if force:
            self.reloadRecords()

    def setSortName(self):
        self.setSort(studiolibrary.SortOption.Name)

    def setSortModified(self):
        self.setSort(studiolibrary.SortOption.Modified)

    def setSortOrdered(self):
        self.setSort(studiolibrary.SortOption.Ordered)

    def plugins(self):
        return self.library().loadedPlugins()

    def plugin(self, name):
        return self.library().loadedPlugins().get(name, None)

    def unloadPlugins(self):
        self.library().unloadPlugins()

    def unloadPlugin(self, name):
        self.library().unloadPlugin(name)

    def loadPlugin(self, name):
        self.library().loadPlugin(name)

    def loadPlugins(self):
        self.library().loadPlugins()

    def clearRecords(self):
        self.recordsWidget().clear()

    def listRecords(self, sort = studiolibrary.SortOption.Ordered):
        """
        :rtype: list[studiolibrary.Record]
        """
        results = []
        folders = self.foldersWidget().selectedFolders()
        for folder in folders:
            path = folder.path()
            records = self.library().listRecords(path)
            if records:
                records = self.library().sortRecords(records, sort=self.sort(), order=folder.order())
                results.extend(records)

        return results

    def reloadRecords(self):
        """
        :rtype: None
        """
        logger.debug("Loading records for library '%s'" % self.library().name())
        elapsedTime = time.time()
        selectedRecords = self.selectedRecords()
        folders = self.foldersWidget().selectedFolders()
        if not folders:
            self.recordsWidget().clear()
        records = self.listRecords()
        self.recordsWidget().setRecords(records)
        if selectedRecords:
            self.selectRecords(selectedRecords)
        if self.selectedRecords() != selectedRecords:
            self.onRecordSelectionChanged()
        elapsedTime = time.time() - elapsedTime
        self.setLoadedMessage(elapsedTime)
        logger.debug('Loaded records')

    def setLoadedMessage(self, elapsedTime):
        """
        :type elapsedTime: time.time
        """
        recordCount = self.ui.recordsWidget.model().recordsCount()
        hiddenCount = self.ui.recordsWidget.model().hiddenRecordsCount()
        plural = ''
        if recordCount != 1:
            plural = 's'
        hiddenText = ''
        if hiddenCount > 0:
            hiddenText = '%d items hidden.' % hiddenCount
        self.ui.statusWidget.setInfo('Loaded %s item%s in %0.3f seconds. %s' % (recordCount,
         plural,
         elapsedTime,
         hiddenText))

    @staticmethod
    def help():
        """
        :rtype: None
        """
        studiolibrary.package().openHelp()

    def deleteSelectedRecords(self):
        """
        :rtype: None
        """
        records = self.recordsWidget().selectedRecords()
        if records:
            result = self.window().questionDialog('Are you sure you want to delete the selected record/s %s' % [ r.name() for r in records ])
            if result == QtGui.QMessageBox.Yes:
                try:
                    for record in records:
                        record.delete()

                except Exception as msg:
                    self.setError(msg)
                finally:
                    self.reloadRecords()

    def deleteSelectedFolders(self):
        """
        :rtype: None
        """
        self.foldersWidget().deleteSelected()

    def showNewMenu(self):
        """
        :rtype: None
        """
        if not self.isLocked():
            point = self.ui.createButton.rect().bottomLeft()
            point = self.ui.createButton.mapToGlobal(point)
            self.ui.newMenu.exec_(point)

    def showSortMenu(self):
        """
        :rtype: None
        """
        point = self.ui.sortButton.rect().bottomLeft()
        point = self.ui.sortButton.mapToGlobal(point)
        self.ui.sortMenu.exec_(point)

    def updateSettingsMenu(self):
        self._libraryActions = []
        self._librariesMenu.reload()

    def showSettingsMenu(self):
        point = self.ui.settingsButton.rect().bottomRight()
        point = self.ui.settingsButton.mapToGlobal(point)
        self.updateSettingsMenu()
        self.ui.settingsMenu.show()
        point.setX(point.x() - self.ui.settingsMenu.width())
        action = self.ui.settingsMenu.exec_(point)

    def isShowFolders(self):
        return self._showFoldersAction.isChecked()

    def setSplitterWidth(self, index, width):
        size = self.ui.splitter.sizes()
        size[index] = width
        self.ui.splitter.setSizes(size)

    def showFolders(self, value):
        if value:
            self.ui.foldersWidget.show()
        else:
            self.ui.foldersWidget.hide()
        self.updateLayout()
        self._showFoldersAction.setChecked(value)

    def showPreview(self, value):
        if value:
            if not self.ui.previewFrame.isVisible():
                self.ui.previewFrame.show()
                if self.ui.previewWidget:
                    self.setPreviewWidget(self.ui.previewWidget)
        else:
            self.ui.previewFrame.hide()
        self._showPreviewAction.setChecked(value)

    def showStatus(self, value):
        """
        :type value: bool
        :rtype: None
        """
        if value:
            if not self.ui.statusWidget.isVisible():
                self.ui.statusWidget.show()
        else:
            self.ui.statusWidget.hide()
        self._showStatusAction.setChecked(value)

    def showMenu(self, value):
        """
        :type value: bool
        """
        if value:
            self.ui.menuFrame.show()
        else:
            self.ui.menuFrame.hide()
        self._showMenuAction.setChecked(value)

    def isShowMenu(self):
        """
        :rtype: bool
        """
        return self._showMenuAction.isChecked()

    def isShowPreview(self):
        """
        :rtype: bool
        """
        return self._showPreviewAction.isChecked()

    def setDebugMode(self, value):
        """
        :type value: bool
        """
        if value:
            self.library().setLoggerLevel(logging.DEBUG)
        else:
            self.library().setLoggerLevel(logging.INFO)

    def showLabels(self, value):
        """
        :type value: bool
        """
        if value:
            self.ui.recordsWidget.showLabels(value)
        else:
            self.ui.recordsWidget.showLabels(False)
        self._showLabelsAction.setChecked(value)

    def showCreateFolderDialog(self):
        """
        :rtype: None
        """
        self.ui.foldersWidget.createFolder(parent=self)