# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\gui\recordswidgetitem.py
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
from PySide import QtGui
from PySide import QtCore
__all__ = ['RecordsWidgetItem']
logger = logging.getLogger(__name__)
DIRNAME = os.path.dirname(__file__)

class RecordsWidgetItem(object):
    ICON_PATH_ERROR = DIRNAME + '/resource/images/thumbnail.png'

    def __init__(self, recordsWidget):
        """
        :type recordsWidget: QtCore.QObject
        """
        self._text = ''
        self._rect = None
        self._pixmap = None
        self._iconPath = ''
        self._recordsWidget = recordsWidget
        return

    def setRecordsWidget(self, recordsWidget):
        """
        :type recordsWidget: QtCore.QObject
        """
        self._recordsWidget = recordsWidget

    def recordsWidget(self):
        """
        :rtype: recordswidget.RecordsWidget
        """
        return self._recordsWidget

    def text(self):
        """
        :rtype: str
        """
        return self._text

    def setText(self, text):
        """
        :type text: str
        """
        self._text = text

    def mousePressEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        logger.debug('mousePressEvent: %s' % self.text())
        return QtGui.QListView.mousePressEvent(self.recordsWidget(), event)

    def mouseReleaseEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        logger.debug('mouseReleaseEvent %s' % self.text())
        return QtGui.QListView.mouseReleaseEvent(self.recordsWidget(), event)

    def mouseMoveEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        pass

    def mouseEnterEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        logger.debug('mouseEnterEvent %s' % self.text())

    def mouseLeaveEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        logger.debug('mouseLeaveEvent %s' % self.text())

    def keyPressEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        logger.debug('keyPressEvent %s' % self.text())

    def keyReleaseEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        logger.debug('keyReleaseEvent %s' % self.text())

    def clicked(self):
        """
        """
        logger.debug('clicked %s' % self.text())

    def doubleClicked(self):
        """
        """
        logger.debug('doubleClicked %s' % self.text())

    def iconPath(self):
        """
        :rtype: str
        """
        return self._iconPath

    def setIconPath(self, path):
        """
        :type path:
        :rtype: None
        """
        self._iconPath = path

    def setPixmap(self, pixmap):
        """
        :type: QtCore.QPixmap
        """
        self._pixmap = pixmap

    def pixmap(self):
        """
        :rtype: QtCore.QPixmap
        """
        if not self._pixmap:
            iconPath = self.iconPath()
            if iconPath:
                if not os.path.exists(iconPath):
                    iconPath = self.ICON_PATH_ERROR
                self._pixmap = QtGui.QPixmap(iconPath)
        return self._pixmap

    def index(self):
        """
        :rtype: int
        """
        return self._index

    def indexData(self, parent, index, role):
        """
        Qt.DisplayRole Text of the item (QString)
        Qt.DecorationRole Icon of the item (QColor, QIcon or QPixmap)
        Qt.EditRole Editing data for editor (QString)
        Qt.ToolTipRole Tooltip of the item (QString)
        Qt.StatusTipRole Text in the status bar (QString)
        Qt.WhatsThisRole Text in "What's This?" mode(QString)
        Qt.SizeHintRole Size hint in view (QSize)
        """
        if role == QtCore.Qt.DisplayRole:
            return self.text()
        if role == QtCore.Qt.DecorationRole:
            return parent.iconSize()

    def textColor(self):
        """
        :rtype: str
        """
        return self.recordsWidget().textColor()

    def textSelectedColor(self):
        """
        :rtype: str
        """
        return self.recordsWidget().textSelectedColor()

    def backgroundColor(self):
        """
        :rtype: str
        """
        return self.recordsWidget().backgroundColor()

    def backgroundSelectedColor(self):
        """
        :rtype: str
        """
        return self.recordsWidget().backgroundSelectedColor()

    def setRect(self, rect):
        """
        :type rect: QtCore.QRect
        """
        self._rect = rect

    def rect(self):
        """
        :rtype: QtCore.QRect
        """
        return self._rect

    def visualRect(self):
        """
        :rtype: QtCore.QRect
        """
        hSpacing = 1
        wSpacing = 1
        r = self.rect()
        if r:
            width = r.width() - wSpacing
            height = r.height() - hSpacing
            return QtCore.QRect(r.x(), r.y(), width, height)
        return self.rect()

    def iconRect(self):
        """
        :rtype: QtGui.QRect
        """
        padding = 2
        marginBottom = 0
        r = self.visualRect()
        isIconView = self.recordsWidget().isIconView()
        isShowLabel = self.recordsWidget().isShowLabels()
        if isShowLabel:
            marginBottom = 15
        if isIconView:
            width = r.width() - padding * 2
            height = r.height() - padding * 2 - marginBottom
        else:
            width = r.height() - padding * 2
            height = r.height() - padding * 2
        return QtCore.QRect(r.x() + padding, r.y() + padding, width, height)

    def textRect(self):
        """
        :rtype: QtGui.QRect
        """
        padding = 2
        r = self.visualRect()
        rect = QtCore.QRect(r.x(), r.y(), r.width(), r.height())
        rect.setLeft(rect.left() + padding)
        rect.setWidth(rect.width() - padding * 2)
        rect.setHeight(rect.height() - padding)
        return rect

    def paintBackground(self, painter, option):
        """
        :type painter: QtGui.QPainter
        :type option:
        """
        isSelected = option.state & QtGui.QStyle.State_Selected
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        if isSelected:
            color = self.backgroundSelectedColor()
            painter.setBrush(QtGui.QBrush(color))
        else:
            color = self.backgroundColor()
            painter.setBrush(QtGui.QBrush(color))
        painter.drawRect(self.visualRect())

    def paintIcon(self, painter, option):
        """
        @param painter: QtGui.QPainter
        @param option:
        """
        pixmap = self.pixmap()
        if isinstance(pixmap, QtGui.QPixmap):
            painter.drawPixmap(self.iconRect(), pixmap)

    def paintText(self, painter, option):
        """
        :type painter: QtGui.QPainter
        :type option:
        """
        text = self.text()
        font = QtGui.QFont()
        rect = self.textRect()
        metrics = QtGui.QFontMetrics(font)
        isListView = self.recordsWidget().isListView()
        isShowLabel = self.recordsWidget().isShowLabels()
        isSelected = option.state & QtGui.QStyle.State_Selected
        if not isShowLabel and not isListView:
            return
        if isListView:
            rect.setLeft(rect.left() + 25)
        if isSelected:
            c = self.textSelectedColor()
            painter.setPen(QtGui.QPen(c))
        else:
            c = self.textColor()
            painter.setPen(QtGui.QPen(c))
        if isListView:
            painter.drawText(rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)
        elif metrics.width(text) > rect.width():
            painter.drawText(rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom, text)
        else:
            painter.drawText(rect, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom, text)

    def paint(self, painter, option):
        """
        :type painter: QtGui.QPainter
        :type option:
        """
        painter.save()
        try:
            self.paintBackground(painter, option)
            self.paintIcon(painter, option)
            self.paintText(painter, option)
        finally:
            painter.restore()

    def repaint(self):
        """
        :rtype: None
        """
        if self.index():
            self.recordsWidget().update(self.index())