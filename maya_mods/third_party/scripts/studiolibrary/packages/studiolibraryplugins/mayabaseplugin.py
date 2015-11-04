#!/usr/bin/python
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
import mutils
import logging
import traceback
import studiolibrary
import selectionsetmenu
from functools import partial

from PySide import QtGui
from PySide import QtCore

try:
    import maya.cmds
except ImportError, msg:
    print msg


__all__ = ["Plugin", "PreviewWidget", "CreateWidget"]
logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Base class for exceptions in this module."""
    pass


class ValidateError(PluginError):
    """"""
    pass


class NamespaceOption:
    FromFile = "pose"
    FromCustom = "custom"
    FromSelection = "selection"


class Plugin(studiolibrary.Plugin):

    def __init__(self, library):
        """
        :type library: studiolibrary.Library
        """
        studiolibrary.Plugin.__init__(self, library)

    @staticmethod
    def tempIconPath(clean=False):
        """
        :rtype: str
        """
        tempDir = studiolibrary.TempDir("icon", clean=clean)
        return tempDir.path() + "/thumbnail.jpg"

    @staticmethod
    def tempIconSequencePath(clean=False):
        """
        :rtype: str
        """
        tempDir = studiolibrary.TempDir("sequence", clean=clean)
        return tempDir.path() + "/thumbnail.jpg"

    @staticmethod
    def createTempIcon():
        """
        :rtype: str
        """
        path = Plugin.tempIconPath()
        return mutils.snapshot(path=path)

    @staticmethod
    def createTempIconSequence(startFrame=None, endFrame=None, step=1):
        """
        :type startFrame: int
        :type endFrame: int
        :type step: int
        :rtype: str
        """
        path = Plugin.tempIconSequencePath(clean=True)

        sequencePath = mutils.snapshot(
            path=path,
            start=startFrame,
            end=endFrame,
            step=step)

        iconPath = Plugin.tempIconPath()
        shutil.copyfile(sequencePath, iconPath)
        return iconPath, sequencePath

    @staticmethod
    def selectionModifiers():
        """
        :rtype: dict[bool]
        """
        result = {"add": False, "deselect": False}
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            result["deselect"] = True
        elif modifiers == QtCore.Qt.ControlModifier:
            result["add"] = True
        return result

    def namespaces(self, record):
        """
        :rtype: list[str]
        """
        return record.namespaces()

    def customNamespaces(self):
        """
        :rtype: list[str]
        """
        return self.settings().get("customNamespaces", "")

    def setCustomNamespaces(self, namespaces):
        """
        :type namespaces: str | list[str]
        """
        if isinstance(namespaces, basestring):
            namespaces = studiolibrary.stringToList(namespaces)

        logger.debug("Setting namespace %s" % namespaces)
        self.settings().set("customNamespaces", namespaces)
        self.settings().save()

    def setNamespaceOption(self, namespaceOption):
        """
        :type namespaceOption: str | NamespaceOption
        """
        logger.debug("Setting namespace option %s" % namespaceOption)
        self.settings().set("namespaceOption", namespaceOption)
        self.settings().save()

    def namespaceOption(self):
        """
        :rtype: NamespaceOption
        """
        return self.settings().get("namespaceOption",
                                   NamespaceOption.FromSelection)

    @mutils.unifyUndo
    def selectContent(self, records=None, namespaces=None):
        """
        :type records: list[studiolibrary.Record]
        """
        records = records or self.libraryWidget().selectedRecords()
        options = Plugin.selectionModifiers()
        for record in records:
            record.selectContent(namespaces=namespaces, **options)

    def setLoggerLevel(self, level):
        """
        :type level: int
        :rtype: None
        """
        logger_ = logging.getLogger("mutils")
        logger_.setLevel(level)

        logger_ = logging.getLogger("studiolibraryplugins")
        logger_.setLevel(level)

    def recordContextMenu(self, menu, records):
        """
        :type menu: QtGui.QMenu
        :type records: list[Record]
        :rtype: None
        """
        if records:
            record = records[-1]

            self.addSelectContentsAction(menu, records)
            menu.addSeparator()

            path = record.path()
            icon = studiolibrary.icon(self.dirname() + "/resource/images/set.png")
            namespaces = record.namespaces()

            subMenu = self.selectionSetsMenu(menu, path=path,
                                             namespaces=namespaces)
            subMenu.setIcon(icon)
            subMenu.setTitle("Selection Sets")

            menu.addMenu(subMenu)
            menu.addSeparator()

    def addSelectContentsAction(self, menu, records=None):
        """
        :type menu: QtGui.QMenu
        :type records: list[studiolibrary.Record]
        :rtype: None
        """
        if records:
            action = self.selectContentsAction(menu, records)
            menu.addAction(action)

    def selectContentsAction(self, menu, records=None):
        """
        :type menu: QtGui.QMenu
        :type records: list[Record]
        """
        icon = studiolibrary.icon(self.dirname() + "/resource/images/arrow.png")
        action = studiolibrary.Action(icon, "Select content", menu)
        trigger = partial(self.selectContent, records)
        action.setCallback(trigger)
        return action

    def selectionSetsMenu(self, parent, path,
                          namespaces=None, includeSelectContents=False):
        """
        :type parent: QtGui.QMenu
        :type path: str
        :type namespaces: list[str]
        :type includeSelectContents: bool
        :rtype: selectionsetmenu.SelectionSetMenu
        """
        selectionSets = self.library().findRecords(path, ".set",
                                                   direction=studiolibrary.Direction.Up)
        menu = selectionsetmenu.SelectionSetMenu("Selection Sets", parent,
                                                 records=selectionSets, namespaces=namespaces)

        if includeSelectContents:
            actions = menu.actions()
            action = self.selectContentsAction(menu)
            if actions:
                firstAction = actions[0]
                menu.insertAction(firstAction, action)
                menu.insertSeparator(firstAction)
            else:
                menu.addAction(action)
        return menu


class Record(studiolibrary.Record):

    def __init__(self, *args, **kwargs):
        """
        :type args: list[]
        :type kwargs: dict[]
        """
        studiolibrary.Record.__init__(self, *args, **kwargs)
        self._transferClass = None
        self._transferObject = None
        self._transferBasename = None

    def prettyPrint(self):
        """
        :rtype: None
        """
        print("------ %s ------" % self.name())
        import json
        print json.dumps(self.transferObject().data(), indent=2)
        print("----------------\n")

    @staticmethod
    def createTempSnapshot():
        """
         Convenience method

        :rtype: str
        """
        return Plugin.createTempSnapshot()

    @staticmethod
    def createTempImageSequence(startFrame, endFrame, step=1):
        """
        Convenience method

        :type startFrame: int
        :type endFrame: int
        :type step: int
        :rtype: str
        """
        return Plugin.createTempImageSequence(startFrame=startFrame,
                                              endFrame=endFrame,
                                              step=step)

    def mirrorTables(self):
        """
        :rtype: str
        """
        return studiolibrary.findPaths(self.path(), ".mirror", direction=studiolibrary.Direction.Up)

    def selectContent(self, namespaces=None, **options):
        """
        :type namespaces: list[str]
        """
        try:
            namespaces = namespaces or self.namespaces()
            options = options or Plugin.selectionModifiers()
            self.transferObject().select(namespaces=namespaces, **options)
        except Exception, msg:
            if self.libraryWidget():
                self.libraryWidget().setError(msg)

    def setTransferClass(self, classname):
        """
        :type classname: mutils.TransferObject
        """
        self._transferClass = classname

    def transferClass(self):
        """
        :rtype:
        """
        return self._transferClass

    def transferPath(self):
        """
        :rtype: str
        """
        if self.transferBasename():
            return "/".join([self.path(), self.transferBasename()])
        else:
            return self.path()

    def transferBasename(self):
        """
        :rtype: str
        """
        return self._transferBasename

    def setTransferBasename(self, transferBasename):
        """
        :rtype: str
        """
        self._transferBasename = transferBasename

    def transferObject(self):
        """
        :rtype: mutils.TransferObject
        """
        if not self._transferObject:
            path = self.transferPath()
            if os.path.exists(path):
                self._transferObject = self.transferClass().fromPath(path)
        return self._transferObject

    def namespaces(self):
        """
        :rtype: list[str]
        """
        namespaceOption = self.plugin().namespaceOption()

        # When creating a new record we can only get the namespaces from
        # selection because the file (transferObject) doesn't exist yet.
        if not self.transferObject():
            return self.namespaceFromSelection()

        # If the file (transferObject) exists then we can use the namespace
        # option to determined which namespaces to return.
        elif namespaceOption == NamespaceOption.FromFile:
            return self.namespaceFromFile()
        elif namespaceOption == NamespaceOption.FromCustom:
            return self.namespaceFromCustom()
        elif namespaceOption == NamespaceOption.FromSelection:
            return self.namespaceFromSelection()

    def namespaceFromFile(self):
        """
        :rtype: list[str]
        """
        return self.transferObject().namespaces()

    def namespaceFromCustom(self):
        """
        :rtype: list[str]
        """
        return self.plugin().customNamespaces()

    @staticmethod
    def namespaceFromSelection():
        """
        :rtype: list[str]
        """
        return mutils.getNamespaceFromSelection() or [""]

    def objectCount(self):
        """
        :rtype: int
        """
        if self.transferObject():
            return self.transferObject().count()
        else:
            return 0

    def doubleClicked(self):
        """
        :rtype: None
        """
        self.load()

    def load(self, objects=None, namespaces=None, **kwargs):
        """
        :type namespaces: list[str]
        :type objects: list[str]
        :rtype: None
        """
        logger.debug("Loading: %s" % self.transferPath())

        self.transferObject().load(objects=objects, namespaces=namespaces, **kwargs)

        logger.debug("Loaded: %s" % self.transferPath())

    def save(self, objects, path=None, iconPath=None, force=False, **kwargs):
        """
        :type path: path
        :type objects: list[]
        :type iconPath: str
        :raise ValidateError:
        """
        logger.info("Saving: {0}".format(path))

        contents = list()
        tempDir = studiolibrary.TempDir("Transfer", clean=True)

        transferPath = tempDir.path() + "/" + self.transferBasename()
        t = self.transferClass().fromObjects(objects)
        t.save(transferPath, **kwargs)

        if iconPath:
            contents.append(iconPath)

        contents.append(transferPath)
        studiolibrary.Record.save(self, path=path, contents=contents, force=force)

        logger.info("Saved: {0}".format(path))


class BaseWidget(QtGui.QWidget):

    def __init__(self, record, libraryWidget=None):
        """
        :type record: Record
        :type libraryWidget: studiolibrary.LibraryWidget
        """
        QtGui.QWidget.__init__(self, None)
        studiolibrary.loadUi(self)

        self._scriptJob = None
        self._record = record
        self._iconPath = ""
        self._libraryWidget = libraryWidget

        self.loadSettings()

        if studiolibrary.isPySide():
            self.layout().setContentsMargins(0, 0, 0, 0)

        if hasattr(self.ui, 'title'):
            self.ui.title.setText(self.record().plugin().name())

        if hasattr(self.ui, 'name'):
            self.ui.name.setText(self.record().name())

        if hasattr(self.ui, 'owner'):
            self.ui.owner.setText(str(self.record().owner()))

        if hasattr(self.ui, 'comment'):
            if isinstance(self.ui.comment, QtGui.QLabel):
                self.ui.comment.setText(self.record().description())
            else:
                self.ui.comment.setPlainText(self.record().description())

        if hasattr(self.ui, "contains"):
            self.updateContains()

        if hasattr(self.ui, 'snapshotButton'):
            path = self.record().iconPath()
            if os.path.exists(path):
                self.setIconPath(self.record().iconPath())

        ctime = self.record().ctime()
        if hasattr(self.ui, 'created') and ctime:
            self.ui.created.setText(studiolibrary.timeAgo(str(ctime)))

        try:
            self.selectionChanged()
            self._scriptJob = mutils.ScriptJob(e=['SelectionChanged', self.selectionChanged])
        except NameError:
            import traceback
            traceback.print_exc()

    def iconPath(self):
        """
        :rtype str
        """
        return self._iconPath

    def setIconPath(self, path):
        """
        :type path: str
        :rtype: None
        """
        self._iconPath = path
        icon = QtGui.QIcon(QtGui.QPixmap(path))
        self.setIcon(icon)

    def setIcon(self, icon):
        """
        :type icon: QtGui.QIcon
        """
        self.ui.snapshotButton.setIcon(icon)
        self.ui.snapshotButton.setIconSize(QtCore.QSize(200, 200))
        self.ui.snapshotButton.setText("")

    def record(self):
        """
        :rtype: Record
        """
        return self._record

    def plugin(self):
        """
        :rtype: Plugin
        """
        return self.record().plugin()

    def settings(self):
        """
        :rtype: studiolibrary.Settings
        """
        return self.plugin().settings()

    def libraryWidget(self):
        """
        :rtype: studiolibrary.LibraryWidget
        """
        return self._libraryWidget

    def showSelectionSetsMenu(self):
        """
        :rtype: None
        """
        folder = self.libraryWidget().selectedFolder()
        if folder:
            path = folder.path()
            self._showSelectionSetsMenu(path)
        else:
            logger.debug("No folder selected! Cannot show the "
                         "selection sets menu because there is no folder selected!")

    def _showSelectionSetsMenu(self, path, includeSelectContents=True):
        """
        :type path: str
        :type includeSelectContents: bool
        :rtype: None
        """
        position = QtGui.QCursor().pos()
        position = self.mapTo(self, position)
        namespaces = self.record().namespaces()
        menu = self.plugin().selectionSetsMenu(self, path=path, namespaces=namespaces,
                                               includeSelectContents=includeSelectContents)
        menu.exec_(position)

    def selectionChanged(self):
        """
        :rtype: None
        """
        pass

    def nameText(self):
        """
        :rtype: str
        """
        return str(self.ui.name.text()).strip()

    def description(self):
        """
        :rtype: str
        """
        return str(self.ui.comment.toPlainText()).strip()

    def loadSettings(self):
        """
        :rtype: None
        """
        pass

    def saveSettings(self):
        """
        :rtype: None
        """
        pass

    def scriptJob(self):
        """
        :rtype: mutils.ScriptJob
        """
        return self._scriptJob

    def close(self):
        """
        :rtype: None
        """
        sj = self.scriptJob()
        if sj:
            sj.kill()
        QtGui.QWidget.close(self)

    def objectCount(self):
        """
        :rtype: int
        """
        return 0

    def updateContains(self):
        """
        :rtype: None
        """
        if not hasattr(self.ui, "contains"):
            return

        count = self.objectCount()
        plural = "s" if count > 1 else ""
        self.ui.contains.setText(str(count) + " Object" + plural)


class InfoWidget(BaseWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        """
        BaseWidget.__init__(self, *args, **kwargs)

        self.setFixedWidth(190)
        self.setFixedHeight(80)

    def objectCount(self):
        """
        :rtype: int
        """
        if self.record().exists():
            return self.record().objectCount()
        return 0


class PreviewWidget(BaseWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        """
        BaseWidget.__init__(self, *args, **kwargs)

        self.connect(self.ui.acceptButton, QtCore.SIGNAL("clicked()"), self.accept)
        self.connect(self.ui.selectionSetButton, QtCore.SIGNAL("clicked()"), self.showSelectionSetsMenu)
        self.connect(self.ui.useFileNamespace, QtCore.SIGNAL("clicked()"), self.stateChanged)
        self.connect(self.ui.useCustomNamespace, QtCore.SIGNAL("clicked()"), self.setFromCustomNamespace)
        self.connect(self.ui.useSelectionNamespace, QtCore.SIGNAL("clicked()"), self.stateChanged)
        self.connect(self.ui.namespaceEdit, QtCore.SIGNAL("textEdited (const QString&)"), self.stateChanged)

        self.ui.selectionSetButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.selectionSetButton.customContextMenuRequested.connect(self.showSelectionSetsMenu)

    def objectCount(self):
        """
        :rtype: int
        """
        if self.record().exists():
            return self.record().objectCount()
        return 0

    def stateChanged(self, state=None):
        """
        :type state: bool
        """
        logger.debug("Preview widget has changed state")
        self.updateNamespaceEdit()
        self.saveSettings()

    def loadSettings(self):
        """
        :rtype: None
        """
        namespaces = self.record().namespaces()
        namespaces = studiolibrary.listToString(namespaces)
        self.ui.namespaceEdit.setText(namespaces)

        namespaceOption = self.plugin().namespaceOption()
        if namespaceOption == NamespaceOption.FromFile:
            self.ui.useFileNamespace.setChecked(True)
        elif namespaceOption == NamespaceOption.FromCustom:
            self.ui.useCustomNamespace.setChecked(True)
        else:
            self.ui.useSelectionNamespace.setChecked(True)

    def saveSettings(self):
        """
        :rtype: None
        """
        if self.ui.useFileNamespace.isChecked():
            self.plugin().setNamespaceOption(NamespaceOption.FromFile)
        elif self.ui.useCustomNamespace.isChecked():
            self.plugin().setNamespaceOption(NamespaceOption.FromCustom)
        else:
            self.plugin().setNamespaceOption(NamespaceOption.FromSelection)

        namespaces = self.namespaces()
        self.plugin().setCustomNamespaces(namespaces)

    def namespaces(self):
        """
        :rtype: list[str]
        """
        return studiolibrary.stringToList(str(self.ui.namespaceEdit.text()))

    def selectionChanged(self):
        """
        :rtype: None
        """
        logger.debug('Updating namespace edit')
        self.updateNamespaceEdit()

    def updateNamespaceEdit(self):
        """
        :rtype: None
        """
        namespaces = None
        if self.ui.useSelectionNamespace.isChecked():
            namespaces = mutils.getNamespaceFromSelection()
        elif self.ui.useFileNamespace.isChecked():
            namespaces = self.record().transferObject().namespaces()

        if not self.ui.useCustomNamespace.isChecked():
            self.ui.namespaceEdit.setEnabled(False)
            self.ui.namespaceEdit.setText(studiolibrary.listToString(namespaces))
        else:
            self.ui.namespaceEdit.setEnabled(True)

    def setFromCustomNamespace(self, value=None):
        """
        :type value:
        """
        self.stateChanged(value)
        if self.ui.useCustomNamespace.isChecked():
            self.ui.namespaceEdit.setFocus()

    def accept(self):
        """
        :rtype: None
        """
        try:
            self.record().load()
        except Exception, msg:
            if self.libraryWidget():
                self.libraryWidget().setError(msg)
            raise


class CreateWidget(BaseWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        """
        BaseWidget.__init__(self, *args, **kwargs)

        self._iconPath = ""
        self._focusWidget = None

        self.connect(self.ui.acceptButton, QtCore.SIGNAL("clicked()"), self.accept)
        self.connect(self.ui.snapshotButton, QtCore.SIGNAL("clicked()"), self.snapshot)
        self.connect(self.ui.selectionSetButton, QtCore.SIGNAL("clicked()"), self.showSelectionSetsMenu)

        self.ui.selectionSetButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.selectionSetButton.customContextMenuRequested.connect(self.showSelectionSetsMenu)

        #modelPanelName = "modelPanelCreateWidget"
        #if maya.cmds.modelPanel(modelPanelName, exists=True, query=True):
        #    maya.cmds.deleteUI(modelPanelName, panel=True)

        #self._modelPanel = mutils.modelpanelwidget.ModelPanelWidget(self, modelPanelName)
        #self._modelPanel.setFixedWidth(160)
        #self._modelPanel.setFixedHeight(160)
        #self.ui.modelPanelLayout.insertWidget(0, self._modelPanel)
        #self.ui.snapshotButton.hide()

    def objectCount(self):
        """
        :rtype: int
        """
        selection = []
        try:
            selection = maya.cmds.ls(selection=True) or []
        except NameError, e:
            traceback.print_exc()

        return len(selection)

    def selectionChanged(self):
        """
        :rtype: None
        """
        self.updateContains()

    def modelPanel(self):
        """
        :rtype: mutils.ModelPanelWidget
        """
        return self._modelPanel

    def snapshot(self):
        """
        :rtype: None
        """
        try:
            path = Plugin.createTempIcon()
            self.setIconPath(path)
        except Exception, msg:
            self.libraryWidget().setError(msg)
            raise

    def snapshotQuestion(self):
        """
        :rtype: int
        """
        title = "Create a snapshot icon"
        message = "Would you like to create a snapshot icon?"
        result = QtGui.QMessageBox.question(self, title, str(message),
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.Ignore |
                                            QtGui.QMessageBox.Cancel)
        if result == QtGui.QMessageBox.Yes:
            self.snapshot()

        return result

    def accept(self):
        """
        :rtype: None
        """
        try:
            name = self.nameText()
            objects = maya.cmds.ls(selection=True) or []
            folder = self.libraryWidget().selectedFolder()

            if not folder:
                raise ValidateError("No folder selected. Please select a destination folder.")

            if not name:
                raise ValidateError("No name specified. Please set a name before saving.")

            if not objects:
                raise ValidateError("No objects selected. Please select at least one object.")

            if not os.path.exists(self.iconPath()):
                result = self.snapshotQuestion()
                if result == QtGui.QMessageBox.Cancel:
                    return

            path = folder.path() + "/" + name
            description = str(self.ui.comment.toPlainText())

            self.save(objects=objects, path=path, iconPath=self.iconPath(),
                      description=description)

        except Exception, msg:
            self.libraryWidget().setError(msg)
            raise

    def save(self, objects, path, iconPath, description):
        """
        :type objects: list[str]
        :type path: str
        :type iconPath: str
        :type description: str
        :rtype: None
        """
        r = self.record()
        r.setDescription(description)
        r.save(objects=objects, path=path, iconPath=iconPath)


if __name__ == "__main__":
    import studiolibrary
    studiolibrary.main()
