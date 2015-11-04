# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\gui\librariesmenu.py
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
import sys
import logging
import studiolibrary
from PySide import QtGui
from PySide import QtCore
__all__ = ['LibrariesMenu']
logger = logging.getLogger(__name__)

class LibrariesMenu(QtGui.QMenu):

    def __init__(self, *args):
        """
        """
        QtGui.QMenu.__init__(self, *args)
        self.reload()

    def reload(self):
        self.clear()
        for library in studiolibrary.libraries():
            action = LibraryAction(self, library)
            self.addAction(action)
            action.setStatusTip('Load library "%s" "%s"' % (library.name(), library.path()))
            action.triggered.connect(library.load)


class LibraryAction(QtGui.QWidgetAction):
    STYLE_SHEET = '\n#actionIcon {\n    background-color: COLOR;\n}\n\n#actionWidget {\n    background-color: BACKGROUND_COLOR;\n}\n\n#actionLabel, #actionLabel, #actionOption {\n    background-color: BACKGROUND_COLOR;\n    color: rgb(255, 255, 255);\n}\n#actionLabel:hover, #actionLabel:hover, #actionOption:hover {\n    background-color: COLOR;\n    color: rgb(255, 255, 255);\n}\n'

    def __init__(self, parent, library):
        """
        :type parent: QtGui.QMenu
        :type library: studiolibrary.Library
        """
        QtGui.QWidgetAction.__init__(self, parent)
        self._library = library
        self.setText(self.library().name())

    def library(self):
        """
        :rtype: studiolibrary.Librarya
        """
        return self._library

    def deleteLibrary(self):
        """
        :rtype: None
        """
        self.parent().close()
        self.library().showDeleteDialog()

    def createWidget(self, parent):
        """
        :type parent: QtGui.QMenu
        """
        height = 25
        spacing = 1
        actionWidget = QtGui.QFrame(parent)
        actionWidget.setObjectName('actionWidget')
        styleSheet = studiolibrary.StyleSheet.fromText(LibraryAction.STYLE_SHEET, options=self.library().theme())
        actionWidget.setStyleSheet(styleSheet.data())
        actionLabel = QtGui.QLabel(self.library().name(), actionWidget)
        actionLabel.setObjectName('actionLabel')
        actionLabel.setFixedHeight(height)
        pixmap = studiolibrary.icon('trash', QtGui.QColor(255, 255, 255, 220), ignoreOverride=True)
        actionOption = QtGui.QPushButton('', actionWidget)
        actionOption.setObjectName('actionOption')
        actionOption.setIcon(pixmap)
        actionOption.setFixedHeight(height + spacing)
        actionOption.setFixedWidth(height)
        actionOption.clicked.connect(self.deleteLibrary)
        actionIcon = QtGui.QLabel('', actionWidget)
        actionIcon.setObjectName('actionIcon')
        actionIcon.setFixedWidth(10)
        actionIcon.setFixedHeight(height)
        actionLayout = QtGui.QHBoxLayout(actionWidget)
        actionLayout.setSpacing(0)
        actionLayout.setContentsMargins(0, 0, 0, 0)
        actionLayout.addWidget(actionIcon, stretch=1)
        actionLayout.addWidget(actionLabel, stretch=1)
        actionLayout.addWidget(actionOption, stretch=1)
        return actionWidget


class Example(QtGui.QMainWindow):

    def __init__(self):
        super(Example, self).__init__()
        menubar = self.menuBar()
        menu = LibrariesMenu('Libraries', menubar)
        menubar.addMenu(menu)
        self.statusBar()
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Menubar')
        self.show()


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(funcName)s: %(message)s', filemode='w')
    app = QtGui.QApplication(sys.argv)
    e = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()