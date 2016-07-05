# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.13.0/build27/studiolibrary\gui\checkforupdatesthread.py
from PySide import QtCore
import studiolibrary
__all__ = ['CheckForUpdatesThread']

class CheckForUpdatesThread(QtCore.QThread):

    def __init__(self, *args):
        QtCore.QThread.__init__(self, *args)

    def run(self):
        if studiolibrary.package().isUpdateAvailable():
            self.emit(QtCore.SIGNAL('updateAvailable()'))