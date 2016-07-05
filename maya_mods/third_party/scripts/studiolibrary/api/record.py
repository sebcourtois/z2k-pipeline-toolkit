# Copyright 2016 by Kurt Rathjen. All Rights Reserved.
#
# Permission to use, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Kurt Rathjen
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# KURT RATHJEN DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# KURT RATHJEN BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import os
import shutil
import logging

from PySide import QtGui
from PySide import QtCore

import studioqt
import studiolibrary


__all__ = ["Record"]

logger = logging.getLogger(__name__)


class RecordError(Exception):
    """"""


class RecordSaveError(RecordError):
    """"""


class RecordLoadError(RecordError):
    """"""


class RecordSignal(QtCore.QObject):
    """"""
    onSaved = QtCore.Signal(object)
    onSaving = QtCore.Signal(object)
    onLoaded = QtCore.Signal(object)
    onDeleted = QtCore.Signal(object)
    onDeleting = QtCore.Signal(object)


class Record(studiolibrary.BasePath, studioqt.ListWidgetItem):

    META_PATH = "{path}/.studioLibrary/record.dict"

    signal = RecordSignal()
    onSaved = signal.onSaved
    onSaving = signal.onSaving
    onLoaded = signal.onLoaded
    onDeleted = signal.onDeleted
    onDeleting = signal.onDeleting

    @classmethod
    def fromPath(cls, path, **kwargs):
        """
        :type path: str
        :rtype: Record
        """
        return cls(path, **kwargs)

    def __init__(
        self,
        path=None,
        plugin=None,
        library=None,
    ):
        """
        :type path: str or None
        :type plugin: studiolibrary.Plugin or None
        :type library: studiolibrary.Library or None
        """
        self._plugin = plugin
        self._library = library
        self._metaFile = None
        self._orderIndex = -1
        self._searchText = None
        self._pluginPixmap = None

        self.setPlugin(plugin)

        studioqt.ListWidgetItem.__init__(self)
        studiolibrary.BasePath.__init__(self, path)

    def delete(self):
        """
        :rtype: None
        """
        raise Exception("Deleting files is not supported!")

    def metaPath(self):
        """
        :rtype: str
        """
        path = self.META_PATH
        return self.resolvePath(path)

    def metaFile(self):
        """
        :rtype: metafile.MetaFile
        """
        path = self.metaPath()

        if self._metaFile:
            if self._metaFile.path() != path:
                self._metaFile.setPath(path)
        else:
            self._metaFile = studiolibrary.MetaFile(path, read=True)

        return self._metaFile

    def setOrderIndex(self, orderIndex):
        """
        :type orderIndex: int
        """
        self._orderIndex = orderIndex

    def orderIndex(self):
        """
        :rtype:
        """
        return self._orderIndex

    def searchText(self):
        """
        :rtype: str
        """
        if not self._searchText:
            self._searchText = str(self.path())
        return self._searchText

    def url(self):
        """
        Used by Studio Library 2.0

        :rtype: str
        """
        url = QtCore.QUrl()
        url.setPath(self.path())
        return url

    def infoWidget(self, parent=None):
        """
        Used by Studio Library 2.0

        :rtype: str
        """
        if self.plugin():
            return self.plugin().infoWidget(parent=parent, record=self)

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

    def rename(self, name, extension=None, force=True):
        """
        :type name: str
        :type force: bool
        :type extension: bool or None
        :rtype: None
        """
        extension = extension or self.extension()
        if name and extension not in name:
            name += extension
        studiolibrary.BasePath.rename(self, name, force=force)

    def setPath(self, path):
        """
        :type path: str
        :rtype: None
        """
        if not path:
            raise RecordError('Cannot set empty record path.')

        text = os.path.basename(path)
        iconPath = path + "/thumbnail.jpg"

        self.setText(text)
        self.setIconPath(iconPath)

        dirname, basename, extension = studiolibrary.splitPath(path)

        if extension:
            if self.plugin():
                if extension != self.plugin().extension():
                    path += self.plugin().extension()
        else:
            if self.plugin():
                path += self.plugin().extension()
            else:
                raise RecordSaveError('No extension found!')

        studiolibrary.BasePath.setPath(self, path)

    def setPlugin(self, plugin):
        """
        :type plugin: studiolibrary.Plugin
        """
        self._plugin = plugin

    def plugin(self):
        """
        :rtype: studiolibrary.Plugin
        """
        return self._plugin

    def description(self):
        """
        :rtype: str
        """
        return self.metaFile().get('description', "")

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
        return self.metaFile().get('owner', "")

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

    def moveContents(self, contents):
        """
        :type contents: list[str]
        """
        path = self.path()

        for src in contents or []:
            basename = os.path.basename(src)
            dst = path + "/" + basename
            logger.info('Moving Content: {0} => {1}'.format(src, dst))
            shutil.move(src, dst)

    def load(self):
        """
        :rtype: None
        """
        logger.debug('Loading "{0}"'.format(self.name()))
        Record.onLoaded.emit(self)

    def save(self, path=None, contents=None):
        """
        :type path: str
        :type contents: list[str]
        :rtype: None
        """
        path = path or self.path()
        contents = contents or []

        logger.debug('Record Saving: {0}'.format(path))
        Record.onSaving.emit(self)

        self.setPath(path)

        if os.path.exists(self.path()):
            raise RecordSaveError("Record already exists!")

        self.metaFile().save()
        self.moveContents(contents)

        Record.onSaved.emit(self)
        logger.debug('Record Saved: {0}'.format(self.path()))

    def showRenameDialog(self, parent=None):
        """
        :type parent: QtGui.QWidget
        """
        parent = parent or self.library()
        name, accepted = QtGui.QInputDialog.getText(
            parent,
            "Rename",
            "New Name",
            QtGui.QLineEdit.Normal,
            self.name()
        )

        if accepted:
            self.rename(str(name))

        return accepted

    def pluginIconRect(self, option):
        """
        :rtype: QtGui.QRect
        """
        padding = 2 * self.dpi()
        r = self.iconRect(option)

        x = r.x() + padding
        y = r.y() + padding
        rect = QtCore.QRect(x, y, 13 * self.dpi(), 13 * self.dpi())

        return rect

    def paintPluginIcon(self, painter, option):
        """
        :type painter: QtGui.QPainter
        :type option:
        """
        rect = self.pluginIconRect(option)

        if not self._pluginPixmap:
            if self.plugin():
                self._pluginPixmap = self.plugin().pixmap()

        if self._pluginPixmap:
            painter.setOpacity(0.5)
            painter.drawPixmap(rect, self._pluginPixmap)

    def paint(self, painter, option, index):
        """
        :type painter: QtGui.QPainter
        :type option:
        """
        studioqt.ListWidgetItem.paint(self, painter, option, index)
        painter.save()
        try:
            self.paintPluginIcon(painter, option)
        finally:
            painter.restore()
