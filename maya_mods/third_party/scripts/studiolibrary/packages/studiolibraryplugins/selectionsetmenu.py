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
import sys
import logging
import studiolibrary
from functools import partial

from PySide import QtGui


__all__ = ["SelectionSetMenu"]
logger = logging.getLogger(__name__)


class SelectionSetMenu(QtGui.QMenu):

    def __init__(self, name, parent, records, **kwargs):
        """
        :type name: str
        :type records: list[studiolibrary.Record]
        :type namespaces: list[str]
        """
        QtGui.QMenu.__init__(self, name, parent)
        self._kwargs = kwargs
        self._records = records
        self.reload()

    def records(self):
        """
        :rtype: list[studiolibrary.Record]
        """
        return self._records

    def reload(self):
        """
        :rtype: None
        """
        self.clear()

        for record in self.records():

            dirname = os.path.basename(record.dirname())
            basename = record.name().replace(record.extension(), "")
            nicename = dirname + ": " + basename

            action = studiolibrary.Action(nicename, self)
            trigger = partial(record.load, **self._kwargs)
            action.setCallback(trigger)
            self.addAction(action)


class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        library = studiolibrary.Library.default()

        menubar = self.menuBar()
        path = "C:/Users/Hovel/Dropbox/libraries/animation/Malcolm/default.pose"
        records = library.findRecords(path, ".set", direction=studiolibrary.Direction.Up)

        menu = SelectionSetMenu("Selection Sets", parent=menubar, records=records)
        menu.setStyleSheet(library.styleSheet())
        menubar.addMenu(menu)

        self.statusBar()
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Menubar')
        self.show()


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(funcName)s: %(message)s',
                        filemode='w')

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()