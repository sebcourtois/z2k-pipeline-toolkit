# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.13.0/build27/studiolibrary\gui\previewwidget.py
from PySide import QtGui
import studioqt
__all__ = ['PreviewWidget']

class PreviewWidget(QtGui.QWidget):

    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        studioqt.loadUi(self)

    def window(self):
        return self.parent().window()