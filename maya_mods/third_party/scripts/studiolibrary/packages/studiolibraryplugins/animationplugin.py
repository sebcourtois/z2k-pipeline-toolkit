# Embedded file name: C:/jipe_Local/z2k-pipeline-toolkit/maya_mods/third_party/scripts/studiolibrary/packages\studiolibraryplugins\animationplugin.py
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

# SAVING AN ANIMATION RECORD

from studiolibraryplugins import animationplugin

path = "/AnimLibrary/Characters/Malcolm/malcolm.anim"
objects = maya.cmds.ls(selection=True) or []

record = animationplugin.Record(path)
record.save(objects=objects, startFrame=0, endFrame=200)


# LOADING AN ANIMATION RECORD

from studiolibraryplugins import animationplugin

path = "/AnimLibrary/Characters/Malcolm/malcolm.anim"
objects = maya.cmds.ls(selection=True) or []
namespaces = []

record = animationplugin.Record(path)
record.load(objects=objects, namespaces=namespaces,
            option="replaceCompletely", connect=False, currentTime=False)

"""
import os
import logging
import mutils
import studiolibrary
import mayabaseplugin
from PySide import QtGui
from PySide import QtCore
try:
    import maya.cmds
except ImportError as msg:
    print msg

logger = logging.getLogger(__name__)
PasteOption = mutils.PasteOption

class AnimationPluginError(Exception):
    """Base class for exceptions in this module."""
    pass


class ValidateAnimationError(AnimationPluginError):
    """"""
    pass


class Plugin(mayabaseplugin.Plugin):

    def __init__(self, library):
        """
        :type library: studiolibrary.Library
        """
        mayabaseplugin.Plugin.__init__(self, library)
        self.setName('Animation')
        self.setExtension('anim')
        self.setIconPath(self.dirname() + '/resource/images/animation.png')
        self.setRecord(Record)
        self.setInfoWidget(AnimationInfoWidget)
        self.setCreateWidget(AnimationCreateWidget)
        self.setPreviewWidget(AnimationPreviewWidget)
        settings = self.settings()
        settings.setdefault('byFrame', 1)
        settings.setdefault('byFrameDialog', True)
        settings.setdefault('connect', False)
        settings.setdefault('currentTime', False)
        settings.setdefault('showHelpImage', False)
        settings.setdefault('option', 'replace')


class Record(mayabaseplugin.Record):

    def __init__(self, *args, **kwargs):
        """
        :type args: list[]
        :type kwargs: dict[]
        """
        mayabaseplugin.Record.__init__(self, *args, **kwargs)
        self._imageSequenceTimer = None
        self.setTransferClass(mutils.Animation)
        self.setTransferBasename('')
        return

    def imageSequenceTimer(self):
        """
        :rtype: studiolibrary.SequenceTimer
        """
        return self._imageSequenceTimer

    def setImageSequenceTimer(self, value):
        """
        :type value: studiolibrary.SequenceTimer
        """
        self._imageSequenceTimer = value

    def stop(self):
        """
        :rtype: None
        """
        self.imageSequenceTimer().stop()
        self.repaint()

    def play(self):
        """
        :rtype: None
        """
        if not self.imageSequenceTimer():
            dirname = self.path() + '/sequence'
            sequenceTimer = studiolibrary.ImageSequenceTimer(self.recordsWidget())
            sequenceTimer.setDirname(dirname)
            sequenceTimer.onFrameChanged.connect(self.frameChanged)
            self.setImageSequenceTimer(sequenceTimer)
        self.imageSequenceTimer().start()

    def rename(self, *args, **kwargs):
        """
        :type args: list[]
        :type kwargs: dict[]
        """
        self.setImageSequenceTimer(None)
        mayabaseplugin.Record.rename(self, *args, **kwargs)
        return

    def mouseEnterEvent(self, event):
        """
        :type event: QtGui.QEvent
        """
        mayabaseplugin.Record.mouseEnterEvent(self, event)
        self.play()

    def mouseLeaveEvent(self, event):
        """
        :type event: QtGui.QEvent
        """
        mayabaseplugin.Record.mouseLeaveEvent(self, event)
        self.stop()

    def mouseMoveEvent(self, event):
        """
        :type event: QtGui.QEvent
        """
        mayabaseplugin.Record.mouseMoveEvent(self, event)
        if studiolibrary.isControlModifier():
            x = event.pos().x() - self.rect().x()
            width = self.rect().width()
            percent = 1.0 - float(width - x) / float(width)
            frame = int(self.imageSequenceTimer().duration() * percent)
            self.imageSequenceTimer().setCurrentFrame(frame)
            self.repaint()

    def frameChanged(self, path):
        """
        :type path: str
        """
        if not studiolibrary.isControlModifier():
            self.repaint()

    def playheadColor(self):
        """
        :rtype: str
        """
        return QtGui.QColor(255, 80, 80)

    def paintPlayhead(self, painter, option):
        """
        :type painter: QtGui.QPainter
        :param option:
        """
        if self.imageSequenceTimer().currentFilename():
            r = self.iconRect()
            c = self.playheadColor()
            sequenceTimer = self.imageSequenceTimer()
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QBrush(c))
            if sequenceTimer.percent() <= 0:
                width = 0
            elif sequenceTimer.percent() >= 1:
                width = r.width()
            else:
                width = sequenceTimer.percent() * r.width() - 1
            painter.drawRect(r.x(), r.y(), width, 2)

    def paintIcon(self, painter, option):
        """
        :type painter: QtGui.QPainter
        :param option:
        """
        if self.imageSequenceTimer():
            pixmap = self.pixmap()
            filname = self.imageSequenceTimer().currentFilename()
            if filname:
                pixmap = QtGui.QPixmap(filname)
                self.setPixmap(pixmap)
            if isinstance(pixmap, QtGui.QPixmap):
                painter.drawPixmap(self.iconRect(), pixmap)
            self.paintPlayhead(painter, option)
        else:
            mayabaseplugin.Record.paintIcon(self, painter, option)

    def startFrame(self):
        """
        :rtype: int
        """
        if self.transferObject().isLegacy():
            return int(self.metaFile().get('start'))
        else:
            return self.transferObject().startFrame()

    def endFrame(self):
        """
        :rtype: int
        """
        if self.transferObject().isLegacy():
            return int(self.metaFile().get('end'))
        else:
            return self.transferObject().endFrame()

    def doubleClicked(self):
        """
        :return: None
        """
        self.loadFromSettings()

    def loadFromSettings(self, sourceStart = None, sourceEnd = None):
        """
        :rtype: None
        """
        objects = maya.cmds.ls(selection=True) or []
        namespaces = self.namespaces()
        settings = self.plugin().settings()
        option = str(settings.get('option'))
        connect = bool(settings.get('connect'))
        currentTime = bool(settings.get('currentTime'))
        try:
            self.load(objects=objects, namespaces=namespaces, option=option, sourceStart=sourceStart, sourceEnd=sourceEnd, connect=connect, currentTime=currentTime)
        except Exception as msg:
            if self.libraryWidget():
                self.libraryWidget().setError(msg)
            raise

    def load(self, objects = None, namespaces = None, startFrame = None, currentTime = False, sourceStart = None, sourceEnd = None, option = None, connect = None):
        """
        :type startFrame: bool
        :type sourceStart: int
        :type sourceEnd: int
        :type option: PasteOption
        :type connect: bool
        :rtype: None
        """
        logger.info('Loading: %s' % self.path())
        objects = objects or []
        if sourceStart is None:
            sourceStart = self.startFrame()
        if sourceEnd is None:
            sourceEnd = self.endFrame()
        self.transferObject().load(objects=objects, namespaces=namespaces, currentTime=currentTime, connect=connect, option=option, startFrame=startFrame, sourceTime=(sourceStart, sourceEnd))
        logger.info('Loaded: %s' % self.path())
        return

    def save(self, objects, path = None, contents = None, iconPath = None, startFrame = None, endFrame = None, bakeConnected = False):
        """
        :type contents: list[str]
        :type iconPath: str
        :type startFrame: int
        :type endFrame: int
        :type bakeConnected: bool
        :rtype: None
        """
        contents = contents or list()
        tempDir = studiolibrary.TempDir('Transfer', clean=True)
        tempPath = tempDir.path() + '/transfer.anim'
        t = self.transferClass().fromObjects(objects)
        t.save(tempPath, time=[startFrame, endFrame], bakeConnected=bakeConnected)
        if iconPath:
            contents.append(iconPath)
        contents.extend(t.paths())
        self.metaFile().set('start', startFrame)
        self.metaFile().set('end', endFrame)
        studiolibrary.Record.save(self, path=path, contents=contents)


class AnimationInfoWidget(mayabaseplugin.InfoWidget):

    def __init__(self, record, libraryWidget = None):
        """
        :type record: Record
        :type libraryWidget: studiolibrary.LibraryWidget
        """
        mayabaseplugin.InfoWidget.__init__(self, record, libraryWidget)
        self._record = record
        end = str(record.get('end'))
        start = str(record.get('start'))
        self.ui.start.setText(start)
        self.ui.end.setText(end)


class AnimationCreateWidget(mayabaseplugin.CreateWidget):

    def __init__(self, *args, **kwargs):
        """
        :type args: list[]
        :type kwargs: dict[]
        """
        mayabaseplugin.CreateWidget.__init__(self, *args, **kwargs)
        self._sequencePath = None
        start, end = mutils.currentRange()
        self.ui.sequenceWidget = studiolibrary.ImageSequenceWidget(self)
        iconPath = self.plugin().dirname() + '/resource/images/thumbnail.png'
        self.ui.sequenceWidget.setIcon(QtGui.QIcon(iconPath))
        self.connect(self.ui.sequenceWidget, QtCore.SIGNAL('clicked()'), self.snapshot)
        self.ui.layout().insertWidget(1, self.ui.sequenceWidget)
        self.ui.snapshotButton.parent().hide()
        self.ui.sequenceWidget.setStyleSheet(self.ui.snapshotButton.styleSheet())
        validator = QtGui.QIntValidator(-50000000, 50000000, self)
        self.ui.endFrameEdit.setValidator(validator)
        self.ui.startFrameEdit.setValidator(validator)
        self.ui.endFrameEdit.setText(str(int(end)))
        self.ui.startFrameEdit.setText(str(int(start)))
        self.ui.byFrameEdit.setValidator(QtGui.QIntValidator(1, 1000, self))
        self.ui.byFrameEdit.setText(str(self.settings().get('byFrame')))
        self.connect(self.ui.setEndFrameButton, QtCore.SIGNAL('clicked()'), self.setEndFrame)
        self.connect(self.ui.setStartFrameButton, QtCore.SIGNAL('clicked()'), self.setStartFrame)
        return

    def sequencePath(self):
        """
        :rtype: str
        """
        return self._sequencePath

    def startFrame(self):
        """
        :rtype: int | None
        """
        try:
            return int(float(str(self.ui.startFrameEdit.text()).strip()))
        except ValueError:
            return None

        return None

    def endFrame(self):
        """
        :rtype: int | None
        """
        try:
            return int(float(str(self.ui.endFrameEdit.text()).strip()))
        except ValueError:
            return None

        return None

    def duration(self):
        """
        :rtype: int
        """
        return self.endFrame() - self.startFrame()

    def byFrame(self):
        """
        :rtype: int
        """
        return int(float(self.ui.byFrameEdit.text()))

    def close(self):
        """
        :rtype: None
        """
        self.settings().set('byFrame', self.byFrame())
        self.settings().save()
        mayabaseplugin.CreateWidget.close(self)

    def setEndFrame(self):
        """
        :rtype: None
        """
        start, end = mutils.selectedRange()
        self.ui.endFrameEdit.setText(str(end))

    def setStartFrame(self):
        """
        :rtype: None
        """
        start, end = mutils.selectedRange()
        self.ui.startFrameEdit.setText(str(start))

    def showByFrameDialog(self):
        """
        :rtype: None
        """
        msg = 'To help speed up the playblast you can set the "by frame" to a number greater than 1. For example if the "by frame" is set to 2 it will playblast every second frame.\nWould you like to show this message again?'
        if self.settings().get('byFrameDialog') and self.duration() > 100 and self.byFrame() == 1:
            result = self.libraryWidget().questionDialog(msg, 'Tip')
            if result == QtGui.QMessageBox.Cancel:
                raise Exception('Cancelled!')
            elif result == QtGui.QMessageBox.No:
                self.settings().set('byFrameDialog', False)

    def snapshot(self):
        """
        :raise: AnimationPluginError
        """
        startFrame, endFrame = mutils.selectedRange()
        if startFrame == endFrame:
            self.validateFrameRange()
            endFrame = self.endFrame()
            startFrame = self.startFrame()
        self.showByFrameDialog()
        try:
            step = self.byFrame()
            iconPath, sequencePath = Plugin.createTempIconSequence(startFrame=startFrame, endFrame=endFrame, step=step)
        except Exception as msg:
            self.libraryWidget().setError(msg)
            raise

        self.setIconPath(iconPath)
        self.setSequencePath(sequencePath)

    def setSequencePath(self, path):
        """
        :type path: str
        :rtype: None
        """
        self._sequencePath = path
        self.ui.sequenceWidget.setDirname(os.path.dirname(path))

    def validateFrameRange(self):
        """
        :raise: ValidateAnimationError
        """
        if self.startFrame() is None or self.endFrame() is None:
            msg = 'Please choose a start frame and an end frame.'
            raise ValidateAnimationError(msg)
        return

    def validateUnknownNodes(self):
        """
        :raise: ValidateAnimationError
        """
        unknown = maya.cmds.ls(type='unknown')
        if unknown:
            msg = 'Found %s unknown node/s in the current scene.\nPlease fix or remove all unknown nodes before saving.\n' % len(unknown)
            logger.info('Unknown nodes: ' + str(unknown))
            raise ValidateAnimationError(msg)

    def save(self, objects, path, iconPath, description):
        """
        :type objects: list[str]
        :type path: str
        :type iconPath: str
        :type description: str
        :rtype: None
        """
        endFrame = self.endFrame()
        startFrame = self.startFrame()
        bakeConnected = int(self.ui.bakeCheckBox.isChecked())
        self.validateUnknownNodes()
        record = self.record()
        record.setDescription(description)
        iconPath = self.iconPath()
        contents = [os.path.dirname(self.sequencePath())]
        record.save(objects=objects, path=path, contents=contents, iconPath=iconPath, startFrame=startFrame, endFrame=endFrame, bakeConnected=bakeConnected)


class AnimationPreviewWidget(mayabaseplugin.PreviewWidget):

    def __init__(self, record, libraryWidget = None):
        """
        :type record: Record
        :type libraryWidget: studiolibrary.LibraryWidget
        """
        mayabaseplugin.PreviewWidget.__init__(self, record=record, libraryWidget=libraryWidget)
        startFrame = str(record.startFrame())
        endFrame = str(record.endFrame())
        self.ui.start.setText(startFrame)
        self.ui.end.setText(endFrame)
        self.ui.sourceStartEdit.setText(startFrame)
        self.ui.sourceEndEdit.setText(endFrame)
        self.connect(self.ui.currentTime, QtCore.SIGNAL('stateChanged (int)'), self.stateChanged)
        self.connect(self.ui.helpCheckBox, QtCore.SIGNAL('stateChanged(int)'), self.showHelpImage)
        self.connect(self.ui.connectCheckBox, QtCore.SIGNAL('stateChanged(int)'), self.connectChanged)
        self.connect(self.ui.option, QtCore.SIGNAL('currentIndexChanged(const QString&)'), self.optionChanged)
        self.loadSettings()

    def sourceStart(self):
        """
        :rtype int
        """
        return int(self.ui.sourceStartEdit.text())

    def sourceEnd(self):
        """
        :rtype int
        """
        return int(self.ui.sourceEndEdit.text())

    def showHelpImage(self, value, save = True):
        """
        :type value:
        :type save:
        """
        if value:
            self.ui.helpImage.show()
        else:
            self.ui.helpImage.hide()
        if save:
            self.saveSettings()

    def saveSettings(self):
        """
        :rtype: None
        """
        super(AnimationPreviewWidget, self).saveSettings()
        s = self.settings()
        s.set('option', str(self.ui.option.currentText()))
        s.set('currentTime', bool(self.ui.currentTime.isChecked()))
        s.set('connect', float(self.ui.connectCheckBox.isChecked()))
        s.set('showHelpImage', bool(self.ui.helpCheckBox.isChecked()))
        s.save()

    def loadSettings(self):
        """
        :rtype: None
        """
        super(AnimationPreviewWidget, self).loadSettings()
        s = self.settings()
        self.ui.currentTime.setChecked(s.get('currentTime'))
        self.ui.connectCheckBox.setChecked(s.get('connect'))
        self.optionChanged(s.get('option'), save=False)
        self.ui.helpCheckBox.setChecked(s.get('showHelpImage'))
        self.showHelpImage(s.get('showHelpImage'), save=False)

    def connectChanged(self, value):
        """
        :type value: bool
        """
        self.optionChanged(str(self.ui.option.currentText()))

    def optionChanged(self, text, save = True):
        """
        :type text: str
        """
        imageText = text
        if text == 'replace all':
            imageText = 'replaceCompletely'
            self.ui.connectCheckBox.setEnabled(False)
        else:
            self.ui.connectCheckBox.setEnabled(True)
        connect = ''
        if self.ui.connectCheckBox.isChecked() and text != 'replace all':
            connect = 'Connect'
        optionImage = os.path.join(self.record().plugin().dirname(), 'resource/images/%s%s.png' % (imageText, connect))
        self.ui.helpImage.setIcon(QtGui.QIcon(optionImage))
        index = self.ui.option.findText(text)
        if index:
            self.ui.option.setCurrentIndex(index)
        if save:
            self.saveSettings()

    def accept(self):
        """
        :rtype: None
        """
        sourceStart = self.sourceStart()
        sourceEnd = self.sourceEnd()
        self.record().loadFromSettings(sourceStart=sourceStart, sourceEnd=sourceEnd)