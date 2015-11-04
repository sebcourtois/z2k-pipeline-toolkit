#!/usr/bin/python
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
import mutils
import mayabaseplugin


from PySide import QtGui


class PluginError(Exception):
    """Base class for exceptions in this module."""
    pass


class Plugin(mayabaseplugin.Plugin):

    def __init__(self, library):
        """
        :type library: studiolibrary.Library
        """
        mayabaseplugin.Plugin.__init__(self, library)

        self.setName("Selection Set")
        self.setIconPath(self.dirname() + "/resource/images/set.png")
        self.setExtension("set")

        self.setRecord(Record)
        self.setInfoWidget(SelectionSetInfoWidget)
        self.setCreateWidget(SelectionSetCreateWidget)
        self.setPreviewWidget(SelectionSetPreviewWidget)


class Record(mayabaseplugin.Record):

    def __init__(self, *args, **kwargs):
        """
        :rtype: None
        """
        mayabaseplugin.Record.__init__(self, *args, **kwargs)
        self.setTransferBasename("set.json")
        self.setTransferClass(mutils.SelectionSet)

        self.setTransferBasename("set.list")
        if not os.path.exists(self.transferPath()):
            self.setTransferBasename("set.json")

    def doubleClicked(self):
        """
        :rtype: None
        """
        self.loadFromSettings()

    def loadFromSettings(self):
        """
        :rtype: None
        """
        namespaces = self.namespaces()
        try:
            self.load(namespaces=namespaces)
        except Exception, msg:
            if self.libraryWidget():
                self.libraryWidget().setError(msg)
            raise

    def load(self, namespaces=None):
        """
        :type namespaces: list[str] | None
        """
        self.selectContent(namespaces=namespaces)


class SelectionSetInfoWidget(mayabaseplugin.InfoWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        :type record: Record
        """
        mayabaseplugin.InfoWidget.__init__(self, *args, **kwargs)


class SelectionSetPreviewWidget(mayabaseplugin.PreviewWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        :type record: Record
        """
        mayabaseplugin.PreviewWidget.__init__(self, *args, **kwargs)

    def accept(self):
        """
        :rtype: None
        """
        self.record().loadFromSettings()


class SelectionSetCreateWidget(mayabaseplugin.CreateWidget):

    def __init__(self, *args, **kwargs):
        """
        :type parent: QtGui.QWidget
        :type record: Record
        """
        mayabaseplugin.CreateWidget.__init__(self, *args, **kwargs)


if __name__ == "__main__":
    import studiolibrary
    studiolibrary.main()
