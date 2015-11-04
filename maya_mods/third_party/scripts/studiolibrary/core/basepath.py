# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\core\basepath.py
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
import utils
import logging
__all__ = ['PathNotFoundError', 'PathRenameError', 'BasePath']
logger = logging.getLogger(__name__)

class PathNotFoundError(IOError):
    """
    """
    pass


class PathRenameError(IOError):
    """
    """
    pass


class BasePath(object):

    def __init__(self, path):
        """
        :type path: str
        """
        path = path or ''
        path.replace('\\', '/')
        self._data = {}
        self._path = ''
        if path:
            self.setPath(path)

    def openLocation(self):
        """
        :rtype: None
        """
        path = self.path()
        utils.openLocation(path)

    def id(self):
        """
        :rtype: str
        """
        return self.path()

    def data(self):
        """
        :rtype: dict[]
        """
        return self._data

    def setData(self, data):
        """
        :type data: dict[]
        :rtype: None
        """
        self._data = data

    def set(self, key, value):
        """
        :type key: str
        :type value: object
        """
        self.data()[key] = value

    def setdefault(self, key, value):
        """
        :type key: str
        :type value: object
        """
        self.data().setdefault(key, value)

    def get(self, key, default = None):
        """
        :type key: str
        :type default: object
        """
        return self.data().get(key, default)

    def path(self):
        """
        :rtype: str
        """
        return self._path

    def setPath(self, path):
        """
        :type path: str
        """
        self._path = path

    def exists(self):
        """
        :rtype: bool
        """
        return os.path.exists(self.path())

    def delete(self):
        """
        """
        if self.exists():
            os.remove(self.path())

    def extension(self):
        """
        :rtype: str
        """
        _, extension = os.path.splitext(self.path())
        return extension

    def dirname(self):
        """
        :rtype: str
        """
        return os.path.dirname(self.path())

    def isFile(self):
        """
        :rtype: bool
        """
        return os.path.isfile(self.path())

    def isFolder(self):
        """
        :rtype: bool
        """
        return os.path.isdir(self.path())

    def name(self):
        """
        :rtype: str
        """
        return os.path.basename(self.path())

    def checkCaseSensitive(self):
        """
        :return:
        """
        for name in os.listdir(self.dirname()):
            logger.debug(name)

    def size(self):
        """
        @return: float
        """
        key = 'size'
        result = self.get(key, None)
        if result is None:
            result = '%.2f' % (os.path.getsize(self.path()) / 1048576.0)
            self.set(key, result)
        return self.get(key, '')

    def mtime(self):
        """
        @return: float
        """
        key = 'mtime'
        result = self.get(key, None)
        if result is None:
            result = os.path.getmtime(self.path())
            self.set(key, result)
        return self.get(key, '')

    def ctime(self):
        """
        @return: float
        """
        key = 'ctime'
        result = self.get(key, None)
        if result is None:
            result = os.path.getctime(self.path())
            self.set(key, result)
        return self.get(key, '')

    def mkdir(self):
        """
        """
        if not os.path.exists(self.dirname()):
            os.makedirs(self.dirname())

    def rename(self, name, extension = None, force = False):
        """
        :type name: str
        :type force: bool
        :rtype:
        """
        dst = name
        src = self.path()
        src = src.replace('\\', '/')
        dst = dst.replace('\\', '/')
        if '/' not in name:
            dst = self.dirname() + '/' + name
        if extension and extension not in name:
            dst += extension
        logger.debug('Renaming: %s => %s' % (src, dst))
        if src == dst and not force:
            raise PathRenameError('The source path and destination path are the same. %s' % src)
        if os.path.exists(dst) and not force:
            raise PathRenameError("Cannot save over an existing path '%s'" % dst)
        if not os.path.exists(self.dirname()):
            raise PathRenameError("The system cannot find the specified path '%s'." % self.dirname())
        if not os.path.exists(os.path.dirname(dst)) and force:
            os.mkdir(os.path.dirname(dst))
        if not os.path.exists(src):
            raise PathRenameError('The system cannot find the specified path %s' % src)
        os.rename(src, dst)
        self.setPath(dst)
        logger.debug('Renamed: %s => %s' % (src, dst))