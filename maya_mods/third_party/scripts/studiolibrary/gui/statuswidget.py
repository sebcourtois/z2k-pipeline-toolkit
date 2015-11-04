# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\gui\statuswidget.py
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
DISPLAY_TIME = 6000

class StatusWidget(QtGui.QWidget):

    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        studiolibrary.loadUi(self)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setObjectName('statusWidget')
        self.setFixedHeight(19)
        self.setMinimumWidth(5)
        self._timer = QtCore.QTimer(self)
        QtCore.QObject.connect(self._timer, QtCore.SIGNAL('timeout()'), self.clear)

    def setError(self, text, msec = DISPLAY_TIME):
        icon = studiolibrary.icon('error14', ignoreOverride=True)
        self.ui.button.setIcon(icon)
        self.ui.message.setStyleSheet('color: rgb(222, 0, 0);')
        self.setText(text, msec)

    def setWarning(self, text, msec = DISPLAY_TIME):
        icon = studiolibrary.icon('warning14', ignoreOverride=True)
        self.ui.button.setIcon(icon)
        self.ui.message.setStyleSheet('color: rgb(222, 180, 0);')
        self.setText(text, msec)

    def setInfo(self, text, msec = DISPLAY_TIME):
        icon = studiolibrary.icon('info14', ignoreOverride=True)
        self.ui.button.setIcon(icon)
        self.ui.message.setStyleSheet('')
        self.setText(text, msec)

    def setText(self, text, msec = DISPLAY_TIME):
        if not text:
            self.clear()
        else:
            self.ui.message.setText(text)
            self._timer.stop()
            self._timer.start(msec)

    def clear(self):
        self._timer.stop()
        self.ui.message.setText('')
        self.ui.message.setStyleSheet('')
        icon = studiolibrary.icon('blank', ignoreOverride=True)
        self.ui.button.setIcon(icon)