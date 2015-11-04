# Embedded file name: C:\jipe_Local\z2k-pipeline-toolkit\maya_mods\third_party\scripts\studiolibrary\api\record.py
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
import shutil
import logging
import studiolibrary
import studiolibrary.gui.recordswidgetitem as recordswidgetitem
from PySide import QtGui
from PySide import QtCore
__all__ = ['Record']
logger = logging.getLogger(__name__)

class RecordError(Exception):
    """"""
    pass


class RecordSaveError(RecordError):
    """"""
    pass


class RecordLoadError(RecordError):
    """"""
    pass


class RecordSignal(QtCore.QObject):
    """"""
    onSaved = QtCore.Signal(object)
    onSaving = QtCore.Signal(object)
    onLoaded = QtCore.Signal(object)
    onDeleted = QtCore.Signal(object)
    onDeleting = QtCore.Signal(object)


class Record(studiolibrary.MasterPath, recordswidgetitem.RecordsWidgetItem):
    META_PATH = '<PATH>/.studioLibrary/record.dict'
    signal = RecordSignal()
    onSaved = signal.onSaved
    onSaving = signal.onSaving
    onLoaded = signal.onLoaded
    onDeleted = signal.onDeleted
    onDeleting = signal.onDeleting

    def __init__(self, path = None, plugin = None, recordsWidget = None, library = None):
        """
        :type recordsWidget: recordswidget.RecordsWidget
        """
        self._plugin = plugin
        self._library = library
        self.setPlugin(plugin)
        recordswidgetitem.RecordsWidgetItem.__init__(self, recordsWidget)
        studiolibrary.MasterPath.__init__(self, path)

    @classmethod
    def fromPath(cls, path, **kwargs):
        """
        :rtype: Record
        """
        return cls(path, **kwargs)

    def library(self):
        """
        :rtype: studiolibrary.Library
        """
        return self._library

    def libraryWidget(self):
        """
        :rtype: studiolibrary.MainWindow
        """
        if self.library():
            return self.library().libraryWidget()

    def clicked(self):
        """
        :rtype: None
        """
        pass

    def contextMenu(self, menu, records):
        """
        :type menu: QtGui.QMenu
        :type records: list[Record]
        :rtype: None
        """
        pass

    def selectionChanged(self, selected, deselected):
        """
        :type selected: list[Record]
        :type deselected: list[Record]
        """
        pass

    def rename(self, name, force = True):
        """
        :type name: str
        :type force: bool
        :rtype: None
        """
        extension = self.extension()
        if name and extension not in name:
            name += extension
        studiolibrary.MasterPath.rename(self, name, force=force)

    def setPath(self, path):
        """
        :type path: str
        :rtype: None
        """
        if not path:
            raise RecordError('Cannot set empty record path.')
        text = os.path.basename(path)
        iconPath = path + '/thumbnail.jpg'
        self.setText(text)
        self.setIconPath(iconPath)
        dirname, basename, extension = studiolibrary.splitPath(path)
        if not extension:
            if self.plugin():
                path += self.plugin().extension()
            else:
                raise RecordSaveError('No extension found!')
        studiolibrary.MasterPath.setPath(self, path)

    def setPlugin(self, plugin):
        """
        :type : studiolibrary.Plugin
        """
        self._plugin = plugin

    def plugin(self):
        """
        :rtype : studiolibrary.Plugin
        """
        return self._plugin

    def mousePressEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        if self.plugin() and self.plugin().infoWindow():
            self.plugin().hideInfoWidget()
        return recordswidgetitem.RecordsWidgetItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        if self.plugin() and self.plugin().infoWindow():
            self.plugin().infoWindow().move(event.globalX() + 15, event.globalY() + 20)

    def mouseEnterEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        if self.plugin() and self.plugin().infoWindow():
            self.plugin().showInfoWidget(self, wait=1500)

    def mouseLeaveEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        if self.plugin() and self.plugin().infoWindow():
            self.plugin().hideInfoWidget()

    def keyPressEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        if self.plugin() and self.plugin().infoWindow():
            self.plugin().hideInfoWidget()

    def keyReleaseEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        if self.plugin() and self.plugin().infoWindow():
            self.plugin().hideInfoWidget()

    def errors(self):
        """
        :rtype: str
        """
        return self.metaFile().errors()

    def description(self):
        """
        :rtype: str
        """
        return self.metaFile().description()

    def setDescription(self, text):
        """
        :type: str
        """
        self.metaFile().setDescription(text)

    def setOwner(self, text):
        """
        :type text: str
        """
        self.metaFile().set('owner', text)

    def owner(self):
        """
        :rtype: str
        """
        return self.metaFile().get('owner', '')

    def mtime(self):
        """
        :rtype: str
        """
        return self.metaFile().mtime()

    def ctime(self):
        """
        :rtype: str
        """
        return self.metaFile().ctime()

    def delete(self):
        """
        The default delete behaviour is to retire and create a version
        of the record. The record/path never gets deleted from the file
        system.
        
        :rtype: None
        """
        logger.debug('Record Deleting: {0}'.format(self.path()))
        Record.onDeleting.emit(self)
        studiolibrary.MasterPath.delete(self)
        Record.onDeleted.emit(self)
        logger.debug('Record Deleted: {0}'.format(self.path()))

    def moveContents(self, contents, destination = None):
        """
        :type contents: list[str]
        """
        if not destination:
            destination = self.path()
        for src in contents or []:
            basename = os.path.basename(src)
            dst = destination + '/' + basename
            logger.info('Moving Content: {0} => {1}'.format(src, dst))
            shutil.move(src, dst)

    def load(self):
        """
        :rtype: None
        """
        logger.debug('Loading "{0}"'.format(self.name()))
        Record.onLoaded.emit(self)

    def save(self, path = None, contents = None, force = False):
        """
        :type contents: list[str]
        :type force: bool
        """
        path = path or self.path()
        contents = contents or []
        logger.debug('Record Saving: {0}'.format(path))
        Record.onSaving.emit(self)
        self.setPath(path)
        if os.path.exists(self.path()):
            if force:
                self.delete()
            elif self.library():
                result = self.showRetireDialog()
                if result != QtGui.QMessageBox.Yes:
                    logger.debug('Dialog Canceled')
                    return
            else:
                raise RecordSaveError('Record already exists!')
        self.metaFile().save()
        self.moveContents(contents)
        Record.onSaved.emit(self)
        logger.debug('Record Saved: {0}'.format(self.path()))

    def showRetireDialog(self, parent = None):
        """
        :type parent: QtGui.QWidget
        """
        parent = parent or self.recordsWidget()
        message = 'The chosen name "{0}" already exists!\n Would you like to create a new version?'.format(self.name())
        result = QtGui.QMessageBox.question(parent, 'Retire Record?', message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
        if result == QtGui.QMessageBox.Yes:
            self.delete()
        return result

    def showRenameDialog(self, parent = None):
        """
        :type parent: QtGui.QWidget
        """
        parent = parent or self.library()
        name, accepted = QtGui.QInputDialog.getText(parent, 'Rename', 'New Name', QtGui.QLineEdit.Normal, self.name())
        if accepted:
            self.rename(str(name))
        return accepted

    def pluginIconRect(self):
        """
        :rtype: QtGui.QRect
        """
        padding = 1
        r = self.iconRect()
        return QtCore.QRect(r.x() + padding, r.y() + padding, 13, 13)

    def paintPluginIcon(self, painter, option):
        """
        :type painter: QtGui.QPainter
        :type option:
        """
        rect = self.pluginIconRect()
        isListView = self.recordsWidget().isListView()
        if not isListView:
            pixmap = self.plugin().pixmap()
            if isinstance(pixmap, QtGui.QPixmap):
                painter.setOpacity(0.5)
                painter.drawPixmap(rect, pixmap)

    def paint(self, painter, option):
        """
        :type painter: QtGui.QPainter
        :type option:
        """
        recordswidgetitem.RecordsWidgetItem.paint(self, painter, option)
        painter.save()
        try:
            self.paintPluginIcon(painter, option)
        finally:
            painter.restore()