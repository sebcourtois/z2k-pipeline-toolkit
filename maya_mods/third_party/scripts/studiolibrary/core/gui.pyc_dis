# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\core\gui.py
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
import resource
from PySide import QtGui
from PySide import QtCore
from PySide import QtUiTools
__all__ = ['image',
 'icon',
 'pixmap',
 'Action',
 'Color',
 'isPySide',
 'StyleSheet',
 'loadUi',
 'isControlModifier']
logger = logging.getLogger(__name__)

def isPySide():
    """
    :rtype: bool
    """
    return True


def mayaWindow():
    """
    :rtype: QtCore.QObject
    """
    try:
        import maya.OpenMayaUI as mui
        import sip
        ptr = mui.MQtUtil.mainWindow()
        return sip.wrapinstance(long(ptr), QtCore.QObject)
    except:
        logger.debug('Warning: Cannot find a maya window.')

    return


class Action(QtGui.QAction):

    def __init__(self, *args):
        """
        """
        QtGui.QAction.__init__(self, *args)
        self.callback = None
        self.args = []
        return

    def setCallback(self, callback, *args):
        """
        """
        self.callback = callback
        self.args = args
        self.connect(self, QtCore.SIGNAL('triggered(bool)'), self.call)

    def call(self, value):
        """
        """
        self.callback(*self.args)


def isControlModifier():
    """
    :rtype: bool
    """
    modifiers = QtGui.QApplication.keyboardModifiers()
    return modifiers == QtCore.Qt.ControlModifier


class Color(QtGui.QColor):

    def toString(self):
        """
        """
        return 'rgb(%d, %d, %d, %d)' % self.getRgb()

    def isDark(self):
        """
        """
        return self.red() < 125 and self.green() < 125 and self.blue() < 125

    @classmethod
    def fromColor(cls, color):
        """
        :type color: QtCore.QColor
        """
        color = 'rgb(%d, %d, %d, %d)' % color.getRgb()
        return cls.fromString(color)

    @classmethod
    def fromString(cls, text):
        """
        :type text: str
        """
        a = 255
        try:
            r, g, b, a = text.replace('rgb(', '').replace(')', '').split(',')
        except ValueError:
            r, g, b = text.replace('rgb(', '').replace(')', '').split(',')

        return cls(int(r), int(g), int(b), int(a))


class StyleSheet:

    def __init__(self):
        """
        """
        self._data = ''

    def setData(self, data):
        """
        :type data: str
        """
        self._data = data

    def data(self):
        """
        :rtype: str
        """
        return self._data

    @classmethod
    def fromPath(cls, path, options = None):
        """
        :param path:
        :return:
        """
        styleSheet = cls()
        data = styleSheet.read(path)
        data = StyleSheet.format(data, options=options)
        styleSheet.setData(data)
        return styleSheet

    @classmethod
    def fromText(cls, text, options = None):
        """
        :param text:
        :return:
        """
        styleSheet = cls()
        data = StyleSheet.format(text, options=options)
        styleSheet.setData(data)
        return styleSheet

    @staticmethod
    def read(path):
        """
        :rtype: str
        """
        p = path
        data = ''
        if p is not None and os.path.exists(p):
            f = open(p, 'r')
            data = f.read()
            f.close()
        return data

    @staticmethod
    def format(data = None, options = None):
        """
        :type options: dict[]
        :rtype: str
        """
        if options is not None:
            keys = options.keys()
            keys.sort(key=len, reverse=True)
            for key in keys:
                data = data.replace(key, options[key])

        return data


def loadUi(widget, path = None):
    """
    :type widget: QWidget || QDialog
    :type path: str
    :rtype: None
    """
    import inspect
    if not path:
        dirname = os.path.dirname(os.path.abspath(inspect.getfile(widget.__class__)))
        basename = widget.__class__.__name__
        path = dirname + '/resource/ui/' + basename + '.ui'
    loadUiPySide(widget, path)


def loadUiPySide(widget, path = None):
    """
    :type widget: QtGui.QWidget
    :type path: str
    :rtype: None
    """
    if os.path.exists(path):
        loader = QtUiTools.QUiLoader()
        loader.setWorkingDirectory(os.path.dirname(path))
        f = QtCore.QFile(path)
        f.open(QtCore.QFile.ReadOnly)
        widget.ui = loader.load(path, widget)
        f.close()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(widget.ui)
        widget.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setMinimumWidth(widget.ui.minimumWidth())
        widget.setMinimumHeight(widget.ui.minimumHeight())
        widget.setMaximumWidth(widget.ui.maximumWidth())
        widget.setMaximumHeight(widget.ui.maximumHeight())


def image(name, extension = 'png'):
    """
    :type name: str
    :type name: extension: str
    :rtype: str
    """
    return resource.Resource.get('images', name + '.' + extension)


def pixmap(path, color = None):
    """
    :type path: str
    :type color: QtGui.QColor
    :rtype: QtGui.QPixmap
    """
    if not os.path.exists(path):
        path = image(path)
    if color:
        alpha = QtGui.QPixmap(path)
        pixmap = QtGui.QPixmap(alpha.size())
        pixmap.fill(color)
        pixmap.setAlphaChannel(alpha.alphaChannel())
        return pixmap
    return QtGui.QPixmap(path)


def icon(path, color = None, ignoreOverride = False):
    """
    :type path: str
    :type color: QtGui.QColor
    :type ignoreOverride: bool
    :rtype: QtGui.QIcon
    """
    icon_ = QtGui.QIcon(pixmap(path, color=color))
    if not ignoreOverride:
        p = pixmap(path, color=QtGui.QColor(222, 222, 222, 155))
        icon_.addPixmap(p, QtGui.QIcon.Disabled, QtGui.QIcon.On)
        p = pixmap(path, color=QtGui.QColor(222, 222, 222, 155))
        icon_.addPixmap(p, QtGui.QIcon.Disabled, QtGui.QIcon.Off)
        p = pixmap(path, color=QtGui.QColor(0, 0, 0, 245))
        icon_.addPixmap(p, QtGui.QIcon.Active, QtGui.QIcon.On)
        p = pixmap(path, color=QtGui.QColor(0, 0, 0, 245))
        icon_.addPixmap(p, QtGui.QIcon.Active, QtGui.QIcon.Off)
        p = pixmap(path, color=QtGui.QColor(0, 0, 0, 245))
        icon_.addPixmap(p, QtGui.QIcon.Selected, QtGui.QIcon.On)
        p = pixmap(path, color=QtGui.QColor(0, 0, 0, 245))
        icon_.addPixmap(p, QtGui.QIcon.Selected, QtGui.QIcon.Off)
    return icon_