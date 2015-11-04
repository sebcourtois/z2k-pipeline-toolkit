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
import studiolibrary

from PySide import QtGui


__all__ = ["Folder"]
logger = logging.getLogger(__name__)


class InvalidPathError(Exception):
    """
    """


class Folder(studiolibrary.MasterPath):

    META_PATH = "<PATH>/.studioLibrary/folder.dict"
    ORDER_PATH = "<PATH>/.studioLibrary/order.list"

    def __init__(self, path):
        """
        :type path: str
        """
        if not path:
            raise InvalidPathError("Invalid folder path specified")

        studiolibrary.MasterPath.__init__(self, path)
        self._pixmap = None

    def save(self, force=False):
        """
        """
        logger.debug("Saving folder '%s'" % self.path())
        if self.exists():
            if force:
                self.retire()
            else:
                raise Exception("Folder already exists!")

        self.metaFile().save()
        logger.debug("Saved folder '%s'" % self.path())

    def reset(self):
        """
        :type: None
        """
        if 'bold' in self.metaFile().data():
            del self.metaFile().data()['bold']

        if 'color' in self.metaFile().data():
            del self.metaFile().data()['color']

        if 'iconPath' in self.metaFile().data():
            del self.metaFile().data()['iconPath']

        if 'iconVisibility' in self.metaFile().data():
            del self.metaFile().data()['iconVisibility']

        self.metaFile().save()
        self._pixmap = None

    def setColor(self, color):
        """
        :type color: QtGui.QColor
        """
        self._pixmap = None
        if isinstance(color, QtGui.QColor):
            color = ('rgb(%d, %d, %d, %d)' % color.getRgb())
        self.metaFile().set("color", color)
        self.metaFile().save()

    def color(self):
        """
        :rtype: QtGui.QColor or None
        """
        color = self.metaFile().get('color', None)
        if color:
            r, g, b, a = eval(color.replace('rgb', ""), {})
            return QtGui.QColor(r, g, b, a)
        else:
            return None

    def setIconVisible(self, value):
        """
        :type value: bool
        """
        self.metaFile().set("iconVisibility", value)
        self.metaFile().save()

    def isIconVisible(self):
        """
        :rtype: bool
        """
        return self.metaFile().get("iconVisibility", True)

    def setBold(self, value, save=True):
        """
        :type value: bool
        :type save: bool
        """
        self.metaFile().set("bold", value)
        if save:
            self.metaFile().save()

    def isBold(self):
        """
        :rtype: bool
        """
        return self.metaFile().get("bold", False)

    def name(self):
        """
        :rtype: str
        """
        return os.path.basename(self.path())

    def setPixmap(self, pixmap):
        """
        :type pixmap: QtGui.QPixmap
        """
        self._pixmap = pixmap

    def setIconPath(self, iconPath):
        """
        :type iconPath: str
        """
        self._pixmap = None
        self.metaFile().set('iconPath', iconPath)
        self.metaFile().save()

    def iconPath(self):
        """
        :rtype: str
        """
        iconPath = self.metaFile().get("icon", None)  # Legacy
        iconPath = self.metaFile().get("iconPath", iconPath)
        if not iconPath:
            return studiolibrary.image("folder")
        return iconPath

    def pixmap(self):
        """
        :rtype: QtGui.QPixmap
        """
        if not self.isIconVisible():
            return studiolibrary.pixmap("")

        if not self._pixmap:
            iconPath = self.iconPath()
            color = self.color()
            if iconPath == studiolibrary.image("folder") and not color:
                color = QtGui.QColor(250, 250, 250, 200)
            self._pixmap = studiolibrary.pixmap(iconPath, color=color)

        return self._pixmap

    def orderPath(self):
        """
        :rtype: str
        """
        path = self.ORDER_PATH
        return self.resolvePath(path)

    def setOrder(self, order):
        """
        :type order: list[str]
        :rtype: None
        """
        path = self.orderPath()
        dirname = os.path.dirname(path)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        f = open(path, "w")
        f.write(str(order))
        f.close()

    def order(self):
        """
        :rtype: list[str]
        """
        path = self.orderPath()
        if os.path.exists(path):
            f = open(path, "r")
            data = f.read()
            f.close()
            if data.strip():
                globals_ = {}
                return eval(data, globals_)
        return []
