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
import logging
import studiolibrary
import studiolibrary.gui

from PySide import QtGui
from PySide import QtCore


__all__ = ["Plugin"]
logger = logging.getLogger(__name__)


class Plugin(studiolibrary.BasePlugin):

    def __init__(self, library, parent=None):
        studiolibrary.BasePlugin.__init__(self, parent)
        self._library = library

        self._iconPath = ""
        self._action = None
        self._pixmap = None
        self._settings = None
        self._extension = None
        self._infoWidget = None
        self._editWidget = None
        self._createWidget = None
        self._previewWidget = None
        self._tracebackWidget = None
        self._currentInfoRecord = None
        self._currentPreviewRecord = None
        self._loggerLevel = logging.NOTSET

        self._recordClass = studiolibrary.Record

        if library.libraryWidget():
            self._infoTimer = QtCore.QTimer(library.libraryWidget())
            self._infoTimer.setSingleShot(True)
            self._infoTimer.connect(self._infoTimer, QtCore.SIGNAL("timeout()"), self._showInfoWidget)

    @staticmethod
    def defaultSettingsPath():
        """
        :rtype: str
        """
        return os.path.join(studiolibrary.Settings.DEFAULT_PATH, "Plugin")

    def settingsPath(self):
        """
        :rtype: str
        """
        return os.path.join(self.defaultSettingsPath(), self.name() + ".dict")

    def setLoggerLevel(self, value):
        """
        :type value: bool
        :rtype: None
        """
        self._loggerLevel = value

    def loggerLevel(self):
        """
        :rtype: bool
        """
        return self._loggerLevel

    def library(self):
        """
        :rtype: studiolibrary.Library
        """
        return self._library

    def load(self):
        """
        :rtype: None
        """
        if self.libraryWidget():
            self._action = QtGui.QAction(studiolibrary.icon(self.iconPath()), self.name(), self.libraryWidget().ui.newMenu)
            self.libraryWidget().connect(self._action, QtCore.SIGNAL("triggered(bool)"), self.showCreateWidget)
            self.libraryWidget().ui.newMenu.addAction(self._action)

    def unload(self):
        """
        :rtype: None
        """
        if self.libraryWidget() and self._action:
            self.libraryWidget().ui.newMenu.removeAction(self._action)
            self._infoTimer.disconnect(self._infoTimer, QtCore.SIGNAL("timeout()"), self._showInfoWidget)

    def match(self, path):
        """
        :type path: str
        :rtype: bool
        """
        if path.endswith(self.extension()):
            return True
        return False

    def pixmap(self):
        """
        :rtype: QtGui.QPixmap
        """
        if not self._pixmap:
            iconPath = self.iconPath()
            if os.path.exists(str(iconPath)):
                self._pixmap = QtGui.QPixmap(iconPath)
        return self._pixmap

    def setExtension(self, extension):
        """
        :type extension: str
        """
        if not extension.startswith("."):
            extension = "." + extension
        self._extension = extension

    def extension(self):
        """
        :rtype : str
        """
        if not self._extension:
            return "." + self.name().lower()
        return self._extension

    def setRecord(self, record):
        """
        :type record:
        :rtype: None
        """
        self._recordClass = record

    def record(self, path=None, recordsWidget=None):
        """
        :rtype: studiolibrary.Record
        """
        library = self.library()

        if not recordsWidget and self.libraryWidget():
            recordsWidget = self.libraryWidget().recordsWidget()

        return self._recordClass(path=path, plugin=self,
                                 library=library, recordsWidget=recordsWidget)

    def settings(self):
        """
        :rtype: studiolibrary.Settings
        """
        if not self._settings:
            self._settings = studiolibrary.MetaFile(self.settingsPath())
        return self._settings

    def findRecords(self, folder, recordsWidget):
        """
        :type recordsWidget: QtGui.QWidget
        :type folder: studiolibrary.Folder
        :rtype: list[studiolibrary.Record]
        """
        return list()

    def setIconPath(self, path):
        """
        :type path: str
        :rtype: None
        """
        self._iconPath = path

    def iconPath(self):
        """
        :rtype: str
        """
        return self._iconPath

    def libraryWidget(self):
        """
        :rtype: studiolibrary.gui.LibraryWidget
        """
        return self.library().libraryWidget()

    def folderSelectionChanged(self, selected, deselected):
        """
        :type selected: list[studiolibrary.Folder]
        :type deselected: list[studiolibrary.Folder]
        :rtype: None
        """
        pass

    def recordSelectionChanged(self, selected, deselected):
        """
        :type selected: list[studiolibrary.Record]
        :type deselected: list[studiolibrary.Record]
        :rtype: None
        """
        pass

    def recordContextMenu(self, menu, records):
        """
        :type menu: QtGui.QMenu
        :type records: list[studiolibrary.Record]
        :rtype: None
        """
        pass

    def infoWindow(self):
        """
        :rtype: QtGui.QWidget
        """
        if self.libraryWidget():
            return self.libraryWidget().ui.infoFrame

    def setInfoWidget(self, widget):
        """
        :type widget: QtGui.QWidget.__class__
        """
        self._infoWidget = widget

    def infoWidget(self, parent, record):
        """
        :type parent: QtGui.QWidget
        :type record: studiolibrary.Record
        :rtype: QtGui.QWidget
        """
        if self.libraryWidget():
            if self._infoWidget:
                return self.loadWidget(self._infoWidget, parent, record)
        return None

    def hideInfoWidget(self):
        """
        :rtype: None
        """
        if self.libraryWidget():
            if self._infoWidget:
                self._infoTimer.stop()
                self._currentInfoRecord = None
                self.libraryWidget().ui.infoFrame.hide()

    def showInfoWidget(self, record, wait=None):
        """
        :type record: studiolibrary.Record
        :type wait: float || None
        :rtype: None
        """
        if self.libraryWidget():
            if self._infoWidget:
                self._currentInfoRecord = record
                if wait:
                    self._infoTimer.start(wait)
                else:
                    self._showInfoWidget()

    def _showInfoWidget(self):
        """
        :rtype: None
        """
        record = self._currentInfoRecord
        parent = self.infoWindow().ui.mainFrame

        self.deleteChildren(parent)
        widget = self.infoWidget(parent, record)

        if widget:
            width = widget.width()
            height = widget.height()

            self.infoWindow().setFixedWidth(width)
            self.infoWindow().setFixedHeight(height)

            self.infoWindow().show()

    def setCreateWidget(self, widget):
        """
        :type widget: QtGui.QWidget.__class__
        :rtype: None
        """
        self._createWidget = widget

    def createWidget(self, libraryWidget, record):
        """
        :type libraryWidget: studiolibrary.libraryWidget
        :type record: studiolibrary.Record
        :rtype: QtGui.QWidget
        """
        return self.loadWidget(self._createWidget, libraryWidget, record)

    def showCreateWidget(self, record=None):
        """
        :type record: studiolibrary.Record
        :rtype: None
        """
        if not record:
            record = self.record()

        _w = self.createWidget(libraryWidget=self.libraryWidget(), record=record)
        self.libraryWidget().setCreateWidget(_w)

    def setEditWidget(self, widget):
        """
        :type widget: QtGui.QWidget.__class__
        :rtype: None
        """
        self._editWidget = widget

    def editWidget(self, parent, record):
        """
        :type parent: QtGui.QWidget
        :type record: studiolibrary.Record
        :rtype: QtGui.QWidget
        """
        return self.loadWidget(self._editWidget, parent, record)

    def showEditWidget(self, parent, record):
        """
        :type parent: QtGui.QWidget
        :type record: studiolibrary.Record
        :rtype: None
        """
        if self._previewWidget:
            if self.libraryWidget().ui.previewWidget:
                self.libraryWidget().ui.previewWidget.close()
            widget = self.editWidget(parent, record)
            self.libraryWidget().setPreviewWidget(widget)

    def setPreviewWidget(self, widget):
        """
        :type widget: QtGui.QWidget.__class__
        :rtype: None
        """
        self._previewWidget = widget

    def previewWidget(self, parent, record):
        """
        :type parent: QtGui.QWidget
        :type record: studiolibrary.Record
        :rtype: QtGui.QWidget
        """
        return self.loadWidget(self._previewWidget, parent, record)

    def showPreviewWidget(self, parent, record):
        """
        :type parent: QtGui.QWidget
        :type record: studiolibrary.Record
        :rtype: None
        """
        if record and record == self.libraryWidget().previewRecord():
            message = 'Preview widget for record "{0}"' \
                      ' is already loaded.'.format(record.name())
            logger.debug(message)
            return

        widget = self.previewWidget(parent, record)
        self.libraryWidget().setPreviewWidget(widget, record)

    def tracebackWidget(self, parent):
        """
        :type parent: QtGui.QWidget
        :rtype: QtGui.QWidget
        """
        if not self._tracebackWidget:
            self._tracebackWidget = studiolibrary.gui.TracebackWidget(parent)
        return self._tracebackWidget

    @staticmethod
    def loadWidget(widget, parent, record):
        """
        :type widget: QtGui.QWidget.__class__
        :type parent: QtGui.QWidget
        :type record: studiolibrary.Record
        :rtype: QtGui.QWidget
        """
        logger.debug('Loading widget for record {name} => {path}'.format(name=record.name(),
                                                                         path=record.path()))
        w = None
        try:
            if record.errors():
                w = studiolibrary.gui.TracebackWidget(None)
                w.setTraceback(record.errors())
            elif widget:
                w = widget(record=record, libraryWidget=parent)
        except Exception, e:
            import traceback
            msg = traceback.format_exc()
            w = studiolibrary.gui.TracebackWidget(None)
            w.setTraceback(msg)
            traceback.print_exc()

        if w and parent:
            parent.layout().addWidget(w)
        return w

    @staticmethod
    def deleteWidget(widget):
        """
        :type widget: QtGui.QWidget
        """
        widget.hide()
        widget.close()
        widget.destroy()
        del widget

    def deleteChildren(self, widget):
        """
        :type widget: QtGui.QWidget
        """
        for i in range(widget.layout().count()):
            child = widget.layout().itemAt(i).widget()
            widget.layout().removeWidget(child)
            self.deleteWidget(child)

