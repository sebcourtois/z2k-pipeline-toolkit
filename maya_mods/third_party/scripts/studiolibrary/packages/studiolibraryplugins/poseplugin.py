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

# SAVING A POSE RECORD

from studiolibraryplugins import poseplugin

path = "/AnimLibrary/Characters/Malcolm/malcolm.pose"
objects = maya.cmds.ls(selection=True) or []

record = poseplugin.Record(path)
record.save(objects=objects)


# LOADING A POSE RECORD

from studiolibraryplugins import poseplugin

path = "/AnimLibrary/Characters/Malcolm/malcolm.pose"
objects = maya.cmds.ls(selection=True) or []
namespaces = []

record = poseplugin.Record(path)
record.load(objects=objects, namespaces=namespaces, key=True, mirror=False)

"""
import os
import math
import mutils
import logging
import mayabaseplugin

from PySide import QtCore

try:
    import maya.cmds
except ImportError, msg:
    print msg


logger = logging.getLogger(__name__)


class Plugin(mayabaseplugin.Plugin):

    def __init__(self, library):
        """
        :type library: studiolibrary.Library
        """
        mayabaseplugin.Plugin.__init__(self, library)

        self.setName("Pose")
        self.setIconPath(self.dirname() + "/resource/images/pose.png")

        self.setRecord(Record)
        self.setInfoWidget(PoseInfoWidget)
        self.setCreateWidget(PoseCreateWidget)
        self.setPreviewWidget(PosePreviewWidget)

    def setKeyOption(self, enable):
        """
        :type enable: bool
        """
        self.settings().set("keyOption", enable)

    def keyOption(self):
        """
        :rtype: bool
        """
        return self.settings().get("keyOption", False)

    def setMirrorOption(self, enable):
        """
        :type enable: bool
        """
        self.settings().set("mirrorOption", enable)

    def mirrorOption(self):
        """
        :rtype: bool
        """
        return self.settings().get("mirrorOption", False)


class Record(mayabaseplugin.Record):

    def __init__(self, *args, **kwargs):
        """
        :type args: list[]
        :type kwargs: dict[]
        """
        mayabaseplugin.Record.__init__(self, *args, **kwargs)

        self._options = None
        self._isLoading = False
        self._autoKeyFrame = None
        self._mousePosition = None
        self._currentBlendValue = 0.0
        self._previousBlendValue = 0.0

        self.setTransferClass(mutils.Pose)
        self.setTransferBasename("pose.dict")
        if not os.path.exists(self.transferPath()):
            self.setTransferBasename("pose.json")

    def isLoading(self):
        """
        :rtype: bool
        """
        return self._isLoading

    def mirrorTable(self):
        """
        :rtype: mutils.MirrorTable
        """
        paths = self.mirrorTables()
        if paths:
            path = paths[0] + "/mirrortable.json"
            return mutils.MirrorTable.fromPath(path)

    def isBlending(self):
        """
        :rtype: bool | None
        """
        return self.mousePosition() is not None

    def currentBlendValue(self):
        """
        :rtype: float
        """
        return self._currentBlendValue

    def previousBlendValue(self):
        """
        :rtype: float
        """
        return self._previousBlendValue

    def toggleMirror(self):
        """
        :rtype: None
        """
        mirror = self.plugin().mirrorOption()
        mirror = False if mirror else True
        self.plugin().setMirrorOption(mirror)
        self.plugin().emit(QtCore.SIGNAL("updateMirror(bool)"), bool(mirror))

    def keyPressEvent(self, event):
        """
        :type event: QtGui.QEvent
        """
        mayabaseplugin.Record.keyPressEvent(self, event)
        if not event.isAutoRepeat():
            if event.key() == QtCore.Qt.Key_M:
                self.toggleMirror()
                blend = self.currentBlendValue()
                mirror = self.plugin().mirrorOption()
                if self.isBlending():
                    self.loadFromSettings(blend=blend, mirror=mirror,
                                          showBlendMessage=True, batchMode=True)
                else:
                    self.loadFromSettings(blend=blend, mirror=mirror, refresh=True)

    def mousePosition(self):
        """
        :rtype: QtGui.QPoint
        """
        return self._mousePosition

    def mousePressEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        mayabaseplugin.Record.mousePressEvent(self, event)
        if event.button() == QtCore.Qt.MidButton:
            self._mousePosition = event.pos()
            blend = self.previousBlendValue()
            self.loadFromSettings(blend=blend, batchMode=True,
                                  showBlendMessage=True)

    def mouseMoveEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        mayabaseplugin.Record.mouseMoveEvent(self, event)
        if self.isBlending():
            value = (event.pos().x() - self.mousePosition().x()) / 1.5
            value = math.ceil(value) + self.previousBlendValue()
            self.loadFromSettings(blend=value, batchMode=True,
                                  showBlendMessage=True)

    def mouseReleaseEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        if self.isBlending():
            blend = self.currentBlendValue()
            self.loadFromSettings(blend=blend, refresh=False)
        mayabaseplugin.Record.mouseReleaseEvent(self, event)

    def selectionChanged(self, *args, **kwargs):
        """
        :rtype: None
        """
        self._mousePosition = None
        self._transferObject = None
        self._previousBlendValue = 0.0
        self.plugin().emit(QtCore.SIGNAL("updateBlend(int)"), int(0.0))

    def beforeLoad(self):
        """
        :rtype: None
        """
        if self._isLoading:
            return

        logger.info('Loading Record "{0}"'.format(self.path()))

        self._isLoading = True

    def afterLoad(self):
        """
        :rtype: None
        """
        if not self._isLoading:
            return

        self._isLoading = False
        self._options = None
        self._mousePosition = None
        self._previousBlendValue = self._currentBlendValue

        logger.info('Loaded Record "{0}"'.format(self.path()))

    def doubleClicked(self):
        """
        :return: None
        """
        self.loadFromSettings(clearSelection=False)

    def loadFromSettings(self, blend=100.0, refresh=True, showBlendMessage=False,
                         batchMode=False, clearSelection=True, mirror=None):
        """
        :type blend: float
        :type refresh: bool
        :type batchMode: bool
        :type clearSelection: bool
        :type showBlendMessage: bool
        """
        if self._options is None:
            plugin = self.plugin()
            self._options = dict()
            self._options["key"] = plugin.keyOption()
            self._options['mirror'] = plugin.mirrorOption()
            self._options['namespaces'] = self.namespaces()
            self._options['mirrorTable'] = self.mirrorTable()
            self._options['objects'] = maya.cmds.ls(selection=True) or []

        if mirror is not None:
            self._options['mirror'] = mirror

        if self.plugin():
            self.plugin().emit(QtCore.SIGNAL("updateBlend(int)"), int(blend))

        try:
            self.load(blend=blend, refresh=refresh, batchMode=batchMode,
                      clearSelection=clearSelection, showBlendMessage=showBlendMessage,
                      **self._options)
        except Exception, msg:
            if self.libraryWidget():
                self.libraryWidget().setError(msg)
            raise

    def load(self, objects=None, namespaces=None, blend=100.0, key=None,
             refresh=True, attrs=None, mirror=None, mirrorTable=None,
             showBlendMessage=False, clearSelection=False, batchMode=False):
        """
        :type objects: list[str]
        :type blend: float
        :type key: bool | None
        :type namespaces: list[str] | None
        :type refresh: bool | None
        :type mirror: bool | None
        :type batchMode: bool
        :type showBlendMessage: bool
        :type mirrorTable: mutils.MirrorTable
        """
        logger.debug("Loading pose '%s'" % self.path())

        self._currentBlendValue = blend

        if showBlendMessage and self.recordsWidget():
            self.recordsWidget().showMessage("Blend: %s%%" % str(blend))

        self.beforeLoad()
        try:
            mayabaseplugin.Record.load(self, objects=objects, namespaces=namespaces, blend=blend,
                                       mirror=mirror, key=key, refresh=refresh, attrs=attrs,
                                       mirrorTable=mirrorTable, clearSelection=clearSelection,
                                       batchMode=batchMode)
        except Exception:
            self.afterLoad()
            raise

        finally:
            if not batchMode:
                self.afterLoad()

        logger.debug("Loaded pose '%s'" % self.path())


class PoseInfoWidget(mayabaseplugin.InfoWidget):

    def __init__(self, *args, **kwargs):
        """"""
        mayabaseplugin.InfoWidget.__init__(self, *args, **kwargs)


class PoseCreateWidget(mayabaseplugin.CreateWidget):
    def __init__(self, *args, **kwargs):
        """"""
        mayabaseplugin.CreateWidget.__init__(self, *args, **kwargs)


class PosePreviewWidget(mayabaseplugin.PreviewWidget):

    def __init__(self, *args, **kwargs):
        """
        :rtype: None
        """
        mayabaseplugin.PreviewWidget.__init__(self, *args, **kwargs)

        self.connect(self.ui.keyCheckBox, QtCore.SIGNAL("clicked()"), self.stateChanged)
        self.connect(self.ui.mirrorCheckBox, QtCore.SIGNAL("clicked()"), self.stateChanged)
        self.connect(self.ui.blendSlider, QtCore.SIGNAL("sliderMoved(int)"), self.sliderMoved)
        self.connect(self.ui.blendSlider, QtCore.SIGNAL("sliderReleased()"), self.sliderReleased)
        self.plugin().connect(self.plugin(), QtCore.SIGNAL("updateBlend(int)"), self.updateSlider)
        self.plugin().connect(self.plugin(), QtCore.SIGNAL("updateMirror(bool)"), self.updateMirror)

        # Mirror check box
        mirrorTip = "Cannot find mirror table!"
        mirrorTable = self.record().mirrorTable()
        if mirrorTable:
            mirrorTip = "Using mirror table: %s" % mirrorTable.path()

        self.ui.mirrorCheckBox.setToolTip(mirrorTip)
        self.ui.mirrorCheckBox.setEnabled(mirrorTable is not None)

    def updateMirror(self, mirror):
        """
        :type mirror: bool
        """
        if mirror:
            self.ui.mirrorCheckBox.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.mirrorCheckBox.setCheckState(QtCore.Qt.Unchecked)

    def loadSettings(self):
        """
        :rtype: None
        """
        mayabaseplugin.PreviewWidget.loadSettings(self)

        key = self.plugin().keyOption()
        mirror = self.plugin().mirrorOption()

        self.ui.keyCheckBox.setChecked(key)
        self.ui.mirrorCheckBox.setChecked(mirror)

    def saveSettings(self):
        """
        :rtype: None
        """
        key = bool(self.ui.keyCheckBox.isChecked())
        mirror = bool(self.ui.mirrorCheckBox.isChecked())

        self.plugin().setKeyOption(key)
        self.plugin().setMirrorOption(mirror)

        mayabaseplugin.PreviewWidget.saveSettings(self)

    def updateSlider(self, value):
        """
        :type value: int
        """
        self.ui.blendSlider.setValue(value)

    def sliderReleased(self):
        """
        :rtype: None
        """
        blend = self.ui.blendSlider.value()
        self.record().loadFromSettings(blend=blend, refresh=False,
                                       showBlendMessage=True)

    def sliderMoved(self, value):
        """
        :type value: float
        """
        self.record().loadFromSettings(blend=value, batchMode=True,
                                       showBlendMessage=True)

    def accept(self):
        """
        :rtype: None
        """
        self.record().loadFromSettings(clearSelection=False)
