# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\gui\recordswidget.py
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
import re
import logging
import recordswidgetitem
from PySide import QtGui
from PySide import QtCore
__all__ = ['RecordsWidget']
logger = logging.getLogger(__name__)

class RecordEvent(QtCore.QEvent):

    def __init__(self, *args):
        QtCore.QEvent.__init__(self, *args)
        self._record = None
        return

    def setRecord(self, record):
        """
        """
        self._record = record

    def record(self):
        """
        """
        return self._record


class MimeData(QtCore.QMimeData):

    def __init__(self, *args):
        QtCore.QMimeData.__init__(self, *args)
        self._records = []

    def hasRecords(self):
        return bool(self._records)

    def setRecords(self, records):
        """
        """
        self._records = records

    def records(self):
        """
        """
        return self._records


class RecordsWidgetSignal(QtCore.QObject):
    """"""
    onOrderChanged = QtCore.Signal()
    onDropped = QtCore.Signal(object)
    onDropping = QtCore.Signal(object)
    onClicked = QtCore.Signal(object)
    onDoubleClicked = QtCore.Signal(object)
    onShowContextMenu = QtCore.Signal()
    onSelectionChanged = QtCore.Signal(object, object)


class RecordsWidget(QtGui.QListView):
    LABEL_HEIGHT = 15
    DRAG_THRESHOLD = 10
    WHEEL_SCROLL_STEP = 5
    DEFAULT_VIEW_SIZE = 90
    DEFAULT_MINIMUM_ICON_SIZE = 20
    DEFAULT_MESSAGE_CORNER_SIZE = 4
    DEFAULT_MESSAGE_COLOR = QtGui.QColor(255, 255, 255)
    DEFAULT_MESSAGE_BACKGROUND_COLOR = QtGui.QColor(0, 0, 0)

    def __init__(self, parent):
        """
        :type parent: QtGui.QWidget
        """
        QtGui.QListView.__init__(self, parent)
        self.signal = RecordsWidgetSignal()
        self.onDropped = self.signal.onDropped
        self.onDropping = self.signal.onDropping
        self.onClicked = self.signal.onClicked
        self.onOrderChanged = self.signal.onOrderChanged
        self.onDoubleClicked = self.signal.onDoubleClicked
        self.onShowContextMenu = self.signal.onShowContextMenu
        self.onSelectionChanged = self.signal.onSelectionChanged
        self._previousSelection = []
        self._drag = None
        self._signalsEnabled = True
        self._viewSize = self.DEFAULT_VIEW_SIZE
        self._zoomIndex = None
        self._zoomAmount = None
        self._minimumIconSize = self.DEFAULT_MINIMUM_ICON_SIZE
        self._messageText = ''
        self._messageAlpha = 255
        self._messageColor = self.DEFAULT_MESSAGE_COLOR
        self._messageCornerSize = self.DEFAULT_MESSAGE_CORNER_SIZE
        self._messageBackgroundColor = self.DEFAULT_MESSAGE_BACKGROUND_COLOR
        self._isLocked = False
        self._buttonDown = None
        self._contextMenu = None
        self._dragAccepted = True
        self._isShowLabels = True
        self._isDropEnabled = True
        self._currentRecord = None
        self._previousRecord = None
        self._dragStartIndex = False
        self._textColor = QtGui.QColor(255, 255, 255)
        self._textSelectedColor = QtGui.QColor(255, 255, 255)
        self._backgroundColor = QtGui.QColor(255, 255, 255, 30)
        self._backgroundSelectedColor = QtGui.QColor(30, 150, 255)
        self._policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.setDragEnabled(True)
        self.setSizePolicy(self._policy)
        self.setSelectionRectVisible(True)
        self.setSpacing(15)
        self.setBatchSize(300)
        self.setMinimumWidth(5)
        self.setMouseTracking(True)
        self.setIconSize(QtCore.QSize(90, 90))
        self.setGridSize(QtCore.QSize(90, 90))
        self.setViewMode(QtGui.QListView.IconMode)
        self.setResizeMode(QtGui.QListView.Adjust)
        self.setLayoutMode(QtGui.QListView.Batched)
        self.updateViewSize()
        delegate = Delegate(self)
        self.setItemDelegate(delegate)
        self.setSelectionMode(QtGui.QListView.ExtendedSelection)
        model = Model([])
        self.setModel(model)
        self._messageDisplayTimer = QtCore.QTimer(self)
        self._messageDisplayTimer.timeout.connect(self.fadeOut)
        self._messageFadeOutTimer = QtCore.QTimer(self)
        self._messageFadeOutTimer.timeout.connect(self._fadeOut)
        self.clicked.connect(self.recordClicked)
        self.doubleClicked.connect(self.recordDoubleClicked)
        return

    def setLocked(self, value):
        """
        :rtype: bool
        """
        self._isLocked = value

    def isLocked(self):
        """
        :rtype: bool
        """
        return self._isLocked

    def addRecord(self, record):
        """
        :param record:
        :return:
        """
        self.model().addRecord(record)

    def setTextColor(self, color):
        """
        :type color: QtGui.QtColor
        :type: None
        """
        self._textColor = color

    def setTextSelectedColor(self, color):
        """
        :type color: QtGui.QtColor
        :type: None
        """
        self._textSelectedColor = color

    def setBackgroundColor(self, color):
        """
        :type color: QtGui.QtColor
        :type: None
        """
        self._backgroundColor = color

    def setBackgroundSelectedColor(self, color):
        """
        :type color: QtGui.QtColor
        :type: None
        """
        self._backgroundSelectedColor = color

    def selectionChanged(self, selected, deselected):
        """
        :type selected: QtGui.QItemSelection
        :type deselected: QtGui.QItemSelection
        """
        indexes1 = selected.indexes()
        selectedRecords = self.recordsFromIndexes(indexes1)
        indexes2 = deselected.indexes()
        deselectedRecords = self.recordsFromIndexes(indexes2)
        records = selectedRecords + deselectedRecords
        for record in records:
            record.selectionChanged(selectedRecords, deselectedRecords)

        if self._signalsEnabled:
            self.onSelectionChanged.emit(selectedRecords, deselectedRecords)

    def recordsFromIndexes(self, indexes):
        """
        :type indexes: list[QtGui.QModelIndex]
        :rtype: recordswidgetitem.RecordsWidgetItem
        """
        result = []
        for index in indexes:
            result.append(self.recordFromIndex(index))

        return result

    def recordFromIndex(self, index):
        """
        :type index: QtGui.QModelIndex
        :rtype: recordswidgetitem.RecordsWidgetItem
        """
        return self.model().recordFromIndex(index)

    def textColor(self):
        """
        :rtype: QtGui.QColor
        """
        return self._textColor

    def textSelectedColor(self):
        """
        :rtype: QtGui.QColor
        """
        return self._textSelectedColor

    def backgroundColor(self):
        """
        :rtype: QtGui.QColor
        """
        return self._backgroundColor

    def backgroundSelectedColor(self):
        """
        :rtype: QtGui.QColor
        """
        return self._backgroundSelectedColor

    def currentRecord(self):
        """
        :rtype: recordswidgetitem.RecordsWidgetItem
        """
        return self._currentRecord

    def previousRecord(self):
        """
        :rtype: recordswidgetitem.RecordsWidgetItem
        """
        return self._previousRecord

    def isListView(self):
        """
        @type: bool
        """
        return self.viewMode() == QtGui.QListView.ListMode

    def isIconView(self):
        """
        :type: bool
        """
        return self.viewMode() == QtGui.QListView.IconMode

    def isShowLabels(self):
        """
        :type: bool
        """
        return self._isShowLabels

    def isDropEnabled(self):
        """
        :rtype: bool
        """
        return self._isDropEnabled and not self.isLocked()

    def minimumIconSize(self):
        """
        :rtype: int
        """
        return self._minimumIconSize

    def records(self):
        """
        :rtype: list[recordswidgetitem.RecordsWidgetItem]
        """
        return self.model().records()

    def fadeOut(self):
        """
        :rtype: None
        """
        self._messageFadeOutTimer.start(1)

    def _fadeOut(self):
        """
        :rtype: None
        """
        alpha = self.messageAlpha()
        logger.debug('Fade out message "%s"' % str(alpha))
        if alpha > 0:
            alpha -= 2
            self.setMessageAlpha(alpha)
            self.repaintMessage()
        else:
            self._messageFadeOutTimer.stop()
            self._messageDisplayTimer.stop()

    def showLabels(self, value):
        """
        :type value: int
        :rtype:
        """
        self._isShowLabels = value
        self.setViewSize(self.viewSize())
        self.repaint()

    def showMessage(self, text, repaint = True):
        """
        :type text: str
        :type repaint: bool
        :rtype: None
        """
        self._messageText = text
        self._messageAlpha = 255
        self._messageDisplayTimer.stop()
        self._messageDisplayTimer.start(500)
        if repaint:
            self.repaintMessage()

    def messageAlpha(self):
        """
        :rtype: float
        """
        return float(self._messageAlpha)

    def setMessageAlpha(self, value):
        """
        :type value: float
        :rtype: None
        """
        self._messageAlpha = value

    def messageFont(self):
        """
        :rtype: QtGui.QFont
        """
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(18)
        return font

    def messageText(self):
        """
        :rtype: str
        """
        return self._messageText

    def messageRect(self, margin = 40):
        """
        :rtype: QtCore.QRect
        """
        font = self.messageFont()
        m = QtGui.QFontMetrics(font)
        text = self.messageText()
        size = self.size()
        w = size.width()
        h = size.height()
        x = w / 2 - m.width(text) / 2
        y = h / 2
        x -= margin / 2
        w = m.width(text) + margin / 2
        return QtCore.QRect(x, y, w, 100)

    def messageCornerSize(self):
        """
        :rtype: int
        """
        return self._messageCornerSize

    def repaintMessage(self):
        """
        :rtype: None
        """
        rect = self.messageRect(margin=100)
        self.repaint(rect)

    def paintEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        QtGui.QListView.paintEvent(self, event)
        if self.messageText() and self.messageAlpha() > 0:
            painter = QtGui.QPainter(self.viewport())
            messageRect = self.messageRect()
            ratio = float(messageRect.width()) / float(messageRect.height())
            yRnd = ratio * messageRect.width() / 100 * self.messageCornerSize()
            xRnd = ratio * messageRect.height() / 100 * self.messageCornerSize()
            painter.setPen(QtCore.Qt.NoPen)
            color = QtGui.QColor(self._messageBackgroundColor)
            color.setAlpha(self.messageAlpha() / 2)
            painter.setBrush(color)
            painter.setRenderHints(QtGui.QPainter.Antialiasing)
            painter.drawRoundRect(messageRect.x(), messageRect.y(), messageRect.width(), messageRect.height(), xRnd, yRnd)
            font = self.messageFont()
            painter.setFont(font)
            color = QtGui.QColor(self._messageColor)
            color.setAlpha(self.messageAlpha())
            painter.setPen(color)
            painter.drawText(messageRect, QtCore.Qt.AlignCenter, self._messageText)

    def setDropEnabled(self, value):
        """
        :type value: bool
        :rtype: None
        """
        self._isDropEnabled = value

    def selectRecord(self, record):
        """
        :type record: recordswidgetitem.RecordsWidgetItem
        :rtype: None
        """
        self.selectRecords([record])

    def clearSelection(self):
        """
        :rtype: None
        """
        self.selectionModel().clearSelection()
        self.repaint()

    def selectRecords(self, records):
        """
        :type records: list[recordswidgetitem.RecordsWidgetItem]
        :rtype: None
        """
        indexes = self.indexesFromRecords(records)
        self.selectIndexes(indexes)

    def selectIndexes(self, indexes):
        """
        :type indexes: list[QtCore.QModelIndex]
        :rtype: None
        """
        self.selectionModel().clearSelection()
        if indexes:
            self._signalsEnabled = False
            for index in indexes[:-1]:
                self.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.Select)

            self._signalsEnabled = True
            self.selectionModel().setCurrentIndex(indexes[-1], QtGui.QItemSelectionModel.Select)

    def recordClicked(self, modelIndex = None):
        """
        :type modelIndex:
        :rtype: None
        """
        record = self.selectedRecord()
        logger.debug('Record clicked "%s"' % record.name())
        if record:
            record.clicked()
            self.onClicked.emit(record)

    def recordDoubleClicked(self, modelIndex = None):
        """
        :type modelIndex:
        :rtype: None
        """
        record = self.selectedRecord()
        logger.debug('Record double clicked "%s"' % record.name())
        if record:
            record.doubleClicked()
            self.onDoubleClicked.emit(record)

    def setViewSize(self, value):
        """
        :type value: int
        :rtype: None
        """
        if self.isShowLabels():
            margin = RecordsWidget.LABEL_HEIGHT
        else:
            margin = 0
        if value < self.minimumIconSize():
            value = self.minimumIconSize()
        self._viewSize = value
        if value > self.minimumIconSize() + 5:
            self.setViewMode(QtGui.QListView.IconMode)
        else:
            value = self.minimumIconSize()
            margin = 0
            self.setViewMode(QtGui.QListView.ListMode)
        self.setIconSize(QtCore.QSize(value, value))
        self.setGridSize(QtCore.QSize(value, value + margin))

    def viewSize(self):
        """
        :rtype: int
        """
        return self._viewSize

    def updateViewSize(self):
        """
        :rtype: None
        """
        self.setViewSize(self.viewSize())

    def selectedRecords(self):
        """
        :rtype: list[recordswidgetitem.RecordsWidgetItem]
        """
        records = []
        for index in self.selectedIndexes():
            record = self.model().records()[index.row()]
            records.append(record)

        return records

    def selectedRecord(self):
        """
        :rtype: studiolibrary.Record or None
        """
        records = self.selectedRecords()
        if records:
            return records[-1]
        else:
            return None

    def clear(self):
        """
        :rtype: None
        """
        if self.model():
            self.model().setRecords([])

    def setRecords(self, records):
        """
        :type records: list[recordswidgetitem.RecordsWidgetItem]
        :rtype: None
        """
        if self.model():
            self.model().setRecords(records)

    def recordHoverEvent(self, record, event):
        """
        :type record: recordswidgetitem.RecordsWidgetItem
        :event event: QtCore.QEvent
        """
        if record:
            record.mouseMoveEvent(event)

    def recordEnterEvent(self, record, event):
        """
        :type record: recordswidgetitem.RecordsWidgetItem
        :event event: QtCore.QEvent
        """
        self._dragStartIndex = None
        if record:
            record.mouseEnterEvent(event)
        return

    def recordLeaveEvent(self, record, event):
        """
        :type record: recordswidgetitem.RecordsWidgetItem
        :event event: QtCore.QEvent
        """
        if record:
            record.mouseLeaveEvent(event)

    def dragEnterEvent(self, event):
        """
        :event event: QtCore.QEvent
        """
        if self.isDropEnabled():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        :event event: QtCore.QEvent
        """
        mimeData = event.mimeData()
        if hasattr(mimeData, 'records') and self.isDropEnabled():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        :type event: QtCore.QEvent
        """
        mimeData = event.mimeData()
        self.onDropping.emit(event)
        if hasattr(mimeData, 'records'):
            records = mimeData.records()
            record = self.recordAt(event.pos())
            if record:
                index = record.index().row()
            else:
                index = -1
            for r in records:
                self.model().removeRecord(r)
                self.model().insertRecord(index, r)

            self.selectRecords(records)
            self.onOrderChanged.emit()
        self.onDropped.emit(event)

    def leaveEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        self.recordLeaveEvent(self._previousRecord, event)
        self._previousRecord = None
        QtGui.QListView.leaveEvent(self, event)
        return

    def keyPressEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        if event.key() == QtCore.Qt.Key_Control:
            self._zoomIndex = None
            self._zoomAmount = None
        for record in self.selectedRecords():
            record.keyPressEvent(event)

        return

    def mousePressEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        self._buttonDown = event.button()
        record = self.recordAt(event.pos())
        if not record:
            if event.button() == QtCore.Qt.LeftButton:
                QtGui.QListView.mousePressEvent(self, event)
                self.clearSelection()
            self._currentRecord = None
        else:
            event._parent = self
            self.recordMousePressEvent(record, event)
        if event.button() == QtCore.Qt.RightButton:
            self.showContextMenu()
        return

    def recordMousePressEvent(self, record, event):
        """
        :type record: recordswidgetitem.RecordsWidgetItem
        :type event: QtCore.QEvent
        :rtype: None
        """
        self._currentRecord = record
        if event.button() == QtCore.Qt.LeftButton:
            self.endDrag()
            self._dragStartPos = event.pos()
            self._dragStartIndex = self.indexAt(event.pos())
            self._previousSelection = self.selectedRecords()
        elif event.button() == QtCore.Qt.RightButton:
            self.endDrag()
            if record is not None:
                record.mousePressEvent(event)
            self._currentRecord = None
        record.mousePressEvent(event)
        return

    def showContextMenu(self):
        """
        :rtype: None
        """
        self.onShowContextMenu.emit()

    def mouseReleaseEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        record = self.recordAt(event.pos())
        event._record = record
        self._buttonDown = None
        if self._currentRecord:
            event._parent = self
            self._currentRecord.mouseReleaseEvent(event)
            self._currentRecord = None
        else:
            QtGui.QListView.mouseReleaseEvent(self, event)
        self.endDrag()
        self.repaint()
        return

    def mouseMoveEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        event._parent = self
        record = self.recordAt(event.pos())
        if self._currentRecord:
            self._currentRecord.mouseMoveEvent(event)
        else:
            self.updateRecordEvent(event)
        if record and not self._drag and self._dragStartIndex and self._dragStartIndex.isValid():
            event._record = self._currentRecord
            self.startDrag(event)
        else:
            QtGui.QListView.mouseMoveEvent(self, event)
        if self._buttonDown:
            self.repaint()

    def updateRecordEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        record = self.recordAt(event.pos())
        if record:
            if id(self._previousRecord) != id(record):
                self.recordLeaveEvent(self._previousRecord, event)
                self.recordEnterEvent(record, event)
            self.recordHoverEvent(record, event)
        elif self._previousRecord:
            self.recordLeaveEvent(self._previousRecord, event)
        self._previousRecord = record

    def wheelEvent(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        numDegrees = event.delta() / 8
        numSteps = numDegrees / 15
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier or modifiers == QtCore.Qt.AltModifier:
            selectedIndexes = self.selectedIndexes()
            if selectedIndexes:
                self._zoomIndex = selectedIndexes[0]
            elif self._zoomAmount is None:
                self._zoomIndex = self.indexAt(QtCore.QPoint(event.pos()))
            self._zoomAmount = numSteps * self.WHEEL_SCROLL_STEP
            value = self.viewSize() + self._zoomAmount
            self.setViewSize(value)
            self.showMessage('Zoom: %s%%' % str(value), repaint=False)
            if self._zoomIndex:
                self.scrollTo(self._zoomIndex, QtGui.QAbstractItemView.PositionAtCenter)
            event.accept()
        else:
            QtGui.QListView.wheelEvent(self, event)
        self.updateRecordEvent(event)
        return

    def selectedUrls(self):
        """
        :rtype: list[QtCore.QUrl]
        """
        urls = []
        for record in self.selectedRecords():
            url = QtCore.QUrl.fromLocalFile(record.path())
            urls.append(url)

        return urls

    def dragPixmap(self, record):
        """
        :type record: recordwidgetitem.RecordWidgetItem
        :rtype: QtGui.QPixmap
        """
        pixmap = QtGui.QPixmap()
        records = self.selectedRecords()
        rect = self.visualRect(record.index())
        pixmap = pixmap.grabWidget(self, rect)
        if len(records) > 1:
            cWidth = 35
            cPadding = 5
            cText = str(len(records))
            cX = pixmap.rect().center().x() - float(cWidth / 2)
            cY = pixmap.rect().top() + cPadding
            cRect = QtCore.QRect(cX, cY, cWidth, cWidth)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(self.backgroundSelectedColor())
            painter.drawEllipse(cRect.center(), float(cWidth / 2), float(cWidth / 2))
            font = QtGui.QFont('Serif', 12, QtGui.QFont.Light)
            painter.setFont(font)
            painter.setPen(self.textSelectedColor())
            painter.drawText(cRect, QtCore.Qt.AlignCenter, str(cText))
        return pixmap

    def startDrag(self, event):
        """
        :type event: QtCore.QEvent
        :rtype: None
        """
        if not self.isDropEnabled():
            logger.debug('Dragging has been disabled!')
            return
        point = self._dragStartPos - event.pos()
        dt = self.DRAG_THRESHOLD
        if point.x() > dt or point.y() > dt or point.x() < -dt or point.y() < -dt:
            record = event._record
            urls = self.selectedUrls()
            pixmap = self.dragPixmap(record)
            records = self.selectedRecords()
            hotSpot = QtCore.QPoint(pixmap.width() / 2, pixmap.height() / 2)
            mimeData = MimeData()
            mimeData.setUrls(urls)
            mimeData.setRecords(records)
            self._drag = QtGui.QDrag(self)
            self._drag.setPixmap(pixmap)
            self._drag.setHotSpot(hotSpot)
            self._drag.setMimeData(mimeData)
            self._drag.start(QtCore.Qt.MoveAction)

    def endDrag(self):
        """
        :rtype: None
        """
        logger.debug('End Drag')
        self._buttonDown = None
        self._dragStartIndex = None
        if self._drag:
            del self._drag
            self._drag = None
        return

    def indexesFromRecords(self, records):
        """
        :type records: list[recordswidgetitem.RecordsWidgetItem]
        :rtype: list[QtCore.QModelIndex]
        """
        indexes = []
        for record in records:
            if isinstance(record, basestring):
                if '/' in record:
                    index = self.model().indexFromPath(record)
                else:
                    index = self.model().indexFromText(record)
            else:
                index = self.model().indexFromPath(record.path())
            if index is not None:
                indexes.append(index)

        return indexes

    def recordAt(self, position):
        """
        :type position: QtCore.QPosition
        :rtype: recordwidgetitem.RecordWidgetItem | None
        """
        index = self.indexAt(position)
        if not index.isValid():
            return
        record = self.model().records()[index.row()]
        if record.rect() and record.rect().contains(position):
            record._index = index
            return record


class Delegate(QtGui.QStyledItemDelegate):

    def __init__(self, *args):
        QtGui.QStyledItemDelegate.__init__(self, *args)

    def paint(self, painter, option, index):
        if index.column() == 0:
            record = index.model().records()[index.row()]
            if record:
                record.setRect(QtCore.QRect(option.rect))
                record.paint(painter, option)


class Model(QtCore.QAbstractTableModel):

    def __init__(self, records, *args):
        QtCore.QAbstractTableModel.__init__(self, *args)
        self._iconSize = QtCore.QSize(90, 90)
        self._filters = [re.compile('.*')]
        self._allRecords = []
        self._filteredRecords = []
        self.setRecords(records)

    def recordsCount(self):
        return len(self._allRecords)

    def hiddenRecordsCount(self):
        return len(self._allRecords) - len(self._filteredRecords)

    def records(self):
        return self._filteredRecords

    def indexFromText(self, text):
        for i, r in enumerate(self.records()):
            if r.text() == text:
                return self.index(i, 0)

    def indexFromPath(self, path):
        for i, r in enumerate(self.records()):
            if r.path() == path:
                return self.index(i, 0)

    def recordFromIndex(self, index):
        return self.records()[index.row()]

    def setRecords(self, records):
        self._allRecords = records or []
        self.update()

    def update(self):
        self._filteredRecords = []
        for record in self._allRecords:
            valid = True
            if valid:
                self._filteredRecords.append(record)

        self.reset()

    def insertRecord(self, i, record):
        if i == -1:
            self.records().append(record)
        else:
            self.records().insert(i, record)

    def removeRecord(self, record):
        for i, r in enumerate(self.records()):
            if id(r) == id(record) or r.path() == record.path():
                self.records().pop(i)

        self.reset()

    def addRecord(self, record):
        self.records().append(record)

    def columnCount(self, index):
        return 1

    def rowCount(self, index):
        return len(self._filteredRecords)

    def setIconSize(self, size):
        size.setHeight(size.height())
        self._iconSize = size

    def iconSize(self):
        return self._iconSize

    def data(self, index, role):
        if index.column() == 0:
            return self.indexData(index, role)
        return QtCore.QVariant()

    def indexData(self, index, role):
        record = self._filteredRecords[index.row()]
        return record.indexData(self, index, role)

    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def removeRow(self, row, index):
        self._filteredRecords.pop(row)
        self.reset()
        return True