#!/usr/bin/python
"""
Released subject to the BSD License
Please visit http://www.voidspace.org.uk/python/license.shtml

Contact: kurt.rathjen@gmail.com
Comments, suggestions and bug reports are welcome.
Copyright (c) 2014, Kurt Rathjen, All rights reserved.

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

# SAVING A MIRROR TABLE RECORD

from studiolibraryplugins import mirrortableplugin

path = "/AnimLibrary/Characters/Malcolm/malcolm.mirror"
objects = maya.cmds.ls(selection=True) or []
leftSide = "Lf"
rightSide = "Rf"

record = mirrortableplugin.Record(path)
record.save(objects=objects, leftSide=leftSide, rightSide=rightSide)


# LOADING A MIRROR TABLE RECORD

from studiolibraryplugins import mirrortableplugin

path = "/AnimLibrary/Characters/Malcolm/malcolm.mirror"
objects = maya.cmds.ls(selection=True) or []
namespaces = []

record = mirrortableplugin.Record(path)
record.load(objects=objects, namespaces=namespaces, animation=True, time=None)

"""
import os
import mutils
import logging
import studiolibrary
import mayabaseplugin

try:
    import maya.cmds
except ImportError, msg:
    print msg

from PySide import QtGui
from PySide import QtCore


logger = logging.getLogger(__name__)
MirrorOption = mutils.MirrorOption


class Plugin(mayabaseplugin.Plugin):

    def __init__(self, library):
        """
        :type library: studiolibrary.Library
        """
        studiolibrary.Plugin.__init__(self, library)

        self.setName("Mirror Table")
        self.setIconPath(self.dirname() + "/resource/images/mirrortable.png")
        self.setExtension("mirror")

        self.setRecord(Record)
        self.setInfoWidget(MirrorTableInfoWidget)
        self.setCreateWidget(MirrorTableCreateWidget)
        self.setPreviewWidget(MirrorTablePreviewWidget)

    def mirrorAnimation(self):
        """
        :rtype: bool
        """
        return self.settings().get("mirrorAnimation", True)

    def mirrorOption(self):
        """
        :rtype: MirrorOption
        """
        return self.settings().get("mirrorOption", MirrorOption.Swap)


class Record(mayabaseplugin.Record):

    def __init__(self, *args, **kwargs):
        """
        :type args:
        :type kwargs:
        """
        mayabaseplugin.Record.__init__(self, *args, **kwargs)
        self.setTransferBasename("mirrortable.json")
        self.setTransferClass(mutils.MirrorTable)

    def keyPressEvent(self, event):
        """
        :type event: 
        """
        if event.key() == QtCore.Qt.Key_M:
            pass

    def doubleClicked(self):
        """
        :rtype: None
        """
        self.loadFromSettings()

    def loadFromSettings(self):
        """
        :rtype: None
        """
        option = self.plugin().mirrorOption()
        animation = self.plugin().mirrorAnimation()
        namespaces = self.namespaces()
        objects = maya.cmds.ls(selection=True) or []

        try:
            self.load(objects=objects, namespaces=namespaces,
                      option=option, animation=animation)
        except Exception, msg:
            if self.libraryWidget():
                self.libraryWidget().setError(msg)
            raise

    @mutils.showWaitCursor
    def load(self, objects=None, namespaces=None, option=None, animation=True, time=None):
        """
        :type objects: list[str]
        :type namespaces: list[str]
        :type option: MirrorOption
        :type animation: bool
        :type time: list[int]
        """
        objects = objects or []
        self.transferObject().load(objects=objects, namespaces=namespaces,
                                   option=option, animation=animation, time=time)

    def save(self, objects, leftSide, rightSide, path=None, iconPath=None):
        """
        :type path: str
        :type objects: list[str]
        :type iconPath: str
        :rtype: None

        """
        logger.info("Saving: %s" % self.transferPath())

        tempDir = studiolibrary.TempDir("Transfer", makedirs=True)
        tempPath = os.path.join(tempDir.path(), self.transferBasename())

        t = self.transferClass().fromObjects(objects, leftSide=leftSide,
                                             rightSide=rightSide)
        t.save(tempPath)

        studiolibrary.Record.save(self, path=path, contents=[tempPath, iconPath])


class MirrorTableInfoWidget(mayabaseplugin.InfoWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        :type record: Record
        """
        mayabaseplugin.InfoWidget.__init__(self, *args, **kwargs)


class MirrorTablePreviewWidget(mayabaseplugin.PreviewWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        :type record: Record
        """
        mayabaseplugin.PreviewWidget.__init__(self, *args, **kwargs)

        self.ui.mirrorAnimationCheckBox.stateChanged.connect(self.stateChanged)
        self.ui.mirrorOptionComboBox.currentIndexChanged.connect(self.stateChanged)

        mt = self.record().transferObject()
        self.ui.left.setText(mt.leftSide())
        self.ui.right.setText(mt.rightSide())

    def mirrorOption(self):
        """
        :rtype: str
        """
        return self.ui.mirrorOptionComboBox.findText(self.ui.mirrorOptionComboBox.currentText(), QtCore.Qt.MatchExactly)

    def mirrorAnimation(self):
        """
        :rtype: bool
        """
        return self.ui.mirrorAnimationCheckBox.isChecked()

    def saveSettings(self):
        """
        """
        super(MirrorTablePreviewWidget, self).saveSettings()
        s = self.settings()
        s.set("mirrorOption", int(self.mirrorOption()))
        s.set("mirrorAnimation", bool(self.mirrorAnimation()))
        s.save()

    def loadSettings(self):
        """
        """
        super(MirrorTablePreviewWidget, self).loadSettings()
        s = self.settings()

        mirrorOption = int(s.get("mirrorOption", MirrorOption.Swap))
        mirrorAnimation = bool(s.get("mirrorAnimation", True))

        self.ui.mirrorOptionComboBox.setCurrentIndex(mirrorOption)
        self.ui.mirrorAnimationCheckBox.setChecked(mirrorAnimation)

    def accept(self):
        """
        :rtype: None
        """
        self.record().loadFromSettings()


class MirrorTableCreateWidget(mayabaseplugin.CreateWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        :type record: Record
        """
        mayabaseplugin.CreateWidget.__init__(self, *args, **kwargs)

    def leftText(self):
        """
        :rtype: str
        """
        return str(self.ui.left.text()).strip()

    def rightText(self):
        """
        :rtype: str
        """
        return str(self.ui.right.text()).strip()

    def selectionChanged(self):
        """
        :rtype: None
        """
        objects = maya.cmds.ls(selection=True) or []

        if not self.ui.left.text():
            self.ui.left.setText(mutils.MirrorTable.findLeftSide(objects))

        if not self.ui.right.text():
            self.ui.right.setText(mutils.MirrorTable.findRightSide(objects))

        mt = mutils.MirrorTable.fromObjects([], leftSide=str(self.ui.left.text()), rightSide=str(self.ui.right.text()))

        self.ui.leftCount.setText(str(mt.leftCount(objects)))
        self.ui.rightCount.setText(str(mt.rightCount(objects)))

        mayabaseplugin.CreateWidget.selectionChanged(self)

    def save(self, objects, path, iconPath, description):
        """
        :type objects: list[str]
        :type path: str
        :type iconPath: str
        :type description: str
        :rtype: None
        """
        leftSide = self.leftText()
        rightSide = self.rightText()
        r = self.record()
        r.setDescription(description)
        self.record().save(objects=objects, leftSide=leftSide,
                           rightSide=rightSide, path=path, iconPath=self.iconPath())


if __name__ == "__main__":
    import studiolibrary
    studiolibrary.main()