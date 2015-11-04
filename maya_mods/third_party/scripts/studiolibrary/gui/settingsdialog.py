# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\gui\settingsdialog.py
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
import studiolibrary
from PySide import QtGui
from PySide import QtCore
__all__ = ['SettingsDialog']

class SettingsDialogSignal(QtCore.QObject):
    """
    """
    onNameChanged = QtCore.Signal(object)
    onPathChanged = QtCore.Signal(object)
    onColorChanged = QtCore.Signal(object)
    onBackgroundColorChanged = QtCore.Signal(object)


class SettingsDialog(QtGui.QDialog):
    """
    """
    signal = SettingsDialogSignal()
    onNameChanged = signal.onNameChanged
    onPathChanged = signal.onPathChanged
    onColorChanged = signal.onColorChanged
    onBackgroundColorChanged = signal.onBackgroundColorChanged

    def __init__(self, parent, library):
        """
        :type parent: QtGui.QWidget
        :type library: studiolibrary.Library
        """
        QtGui.QDialog.__init__(self, parent)
        studiolibrary.loadUi(self)
        self.setWindowTitle('Studio Library - %s' % studiolibrary.version())
        self.ui.saveButton.clicked.connect(self.save)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.browseColorButton.clicked.connect(self.browseColor)
        self.ui.browseLocationButton.clicked.connect(self.browseLocation)
        self.ui.theme1Button.clicked.connect(self.setTheme1)
        self.ui.theme2Button.clicked.connect(self.setTheme2)
        self.ui.theme3Button.clicked.connect(self.setTheme3)
        self.ui.theme4Button.clicked.connect(self.setTheme4)
        self.ui.theme5Button.clicked.connect(self.setTheme5)
        self.ui.theme6Button.clicked.connect(self.setTheme6)
        self.ui.background1Button.clicked.connect(self.setBackground1)
        self.ui.background2Button.clicked.connect(self.setBackground2)
        self.ui.background3Button.clicked.connect(self.setBackground3)
        self._library = library
        self.updateStyleSheet()
        self.center()

    def save(self):
        """
        :rtype: None
        """
        self.validate()
        self.accept()

    def validate(self):
        """
        :rtype: None
        """
        try:
            library = self.library()
            library.validateName(self.name())
            library.validatePath(self.location())
        except Exception as e:
            QtGui.QMessageBox.critical(self, 'Validate Error', str(e))
            raise

    def center(self, width = 600, height = 435):
        """
        :rtype: None
        """
        desktopRect = QtGui.QApplication.desktop().availableGeometry()
        center = desktopRect.center()
        self.setGeometry(0, 0, width, height)
        self.move(center.x() - self.width() * 0.5, center.y() - self.height() * 0.5)

    def library(self):
        """
        :rtype: studiolibrary.Library
        """
        return self._library

    def setTitle(self, text):
        """
        :type text: str
        :rtype: None
        """
        self.ui.title.setText(text)

    def setText(self, text):
        """
        :type text: str
        :rtype: None
        """
        self.ui.text.setText(text)

    def setHeader(self, text):
        """
        :type text: str
        :rtype: None
        """
        self.ui.header.setText(text)

    def color(self):
        """
        :rtype: studiolibrary.Color
        """
        return self.library().color()

    def backgroundColor(self):
        """
        :rtype: studiolibrary.Color
        """
        return self.library().backgroundColor()

    def name(self):
        """
        :rtype: str
        """
        return str(self.ui.nameEdit.text())

    def setName(self, name):
        """
        :type name: str
        :rtype: None
        """
        self.ui.nameEdit.setText(name)

    def setLocation(self, path):
        """
        :type path: str
        """
        self.ui.locationEdit.setText(path)

    def location(self):
        """
        :rtype: str
        """
        return str(self.ui.locationEdit.text())

    def setUpdateEnabled(self, value):
        """
        :type value: bool
        :rtype: None
        """
        self._update = value

    def setTheme1(self):
        """
        """
        c = studiolibrary.Color(0, 175, 255)
        self.setColor(c)

    def setTheme2(self):
        """
        """
        c = studiolibrary.Color(150, 75, 240)
        self.setColor(c)

    def setTheme3(self):
        """
        """
        c = studiolibrary.Color(240, 100, 150)
        self.setColor(c)

    def setTheme4(self):
        """
        """
        c = studiolibrary.Color(240, 75, 50)
        self.setColor(c)

    def setTheme5(self):
        """
        """
        c = studiolibrary.Color(250, 155, 20)
        self.setColor(c)

    def setTheme6(self):
        """
        """
        c = studiolibrary.Color(120, 200, 0)
        self.setColor(c)

    def setBackground1(self):
        """
        """
        c = studiolibrary.Color(80, 80, 80)
        self.setBackgroundColor(c)

    def setBackground2(self):
        """
        """
        c = studiolibrary.Color(65, 65, 65)
        self.setBackgroundColor(c)

    def setBackground3(self):
        """
        """
        c = studiolibrary.Color(50, 50, 50)
        self.setBackgroundColor(c)

    def setColor(self, color):
        """
        :type color: studiolibrary.Color
        :rtype: None
        """
        self.library().setColor(color)
        self.updateStyleSheet()
        self.onColorChanged.emit(self)

    def setBackgroundColor(self, color):
        """
        :type color: studiolibrary.Color
        :rtype: None
        """
        self.library().setBackgroundColor(color)
        self.updateStyleSheet()
        self.onBackgroundColorChanged.emit(self)

    def browseColor(self):
        """
        :rtype: None
        """
        color = self.color()
        d = QtGui.QColorDialog(self)
        d.connect(d, QtCore.SIGNAL('currentColorChanged (const QColor&)'), self.setColor)
        d.open()
        if d.exec_():
            self.setColor(d.selectedColor())
        else:
            self.setColor(color)

    def updateStyleSheet(self):
        """
        :rtype: None
        """
        self.setStyleSheet(self.library().styleSheet())

    def browseLocation(self):
        """
        :rtype: None
        """
        path = self.location()
        path = self.browse(path, title='Browse Location')
        if path:
            self.setLocation(path)

    @staticmethod
    def browse(path, title = 'Browse Location'):
        """
        :type path: str
        :type title: str
        :rtype: str
        """
        if not path:
            from os.path import expanduser
            path = expanduser('~')
        path = str(QtGui.QFileDialog.getExistingDirectory(None, title, path))
        path = path.replace('\\', '/')
        return path