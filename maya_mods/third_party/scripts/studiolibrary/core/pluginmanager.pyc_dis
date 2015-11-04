# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\core\pluginmanager.py
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
import imp
import utils
import logging
from PySide import QtCore
__all__ = ['BasePlugin', 'PluginManager']
logger = logging.getLogger(__name__)

class BasePlugin(QtCore.QObject):

    def __init__(self, parent = None):
        """
        """
        QtCore.QObject.__init__(self, parent)
        self._name = ''
        self._path = ''
        self._loaded = False

    def dirname(self):
        """
        :rtype: str
        """
        import inspect
        return os.path.dirname(inspect.getfile(self.__class__))

    def setName(self, name):
        """
        :type name: str
        :rtype: None
        """
        self._name = name

    def name(self):
        """
        :rtype: str
        """
        return self._name

    def setPath(self, path):
        """
        :type path: str
        """
        self._path = path

    def path(self):
        """
        :rtype: str
        """
        return self._path

    def isLoaded(self):
        """
        :rtype: bool
        """
        return self._loaded

    def setLoaded(self, value):
        """
        :type value: bool
        """
        self._loaded = value

    def load(self):
        """
        :rtype: None
        """
        pass

    def unload(self):
        """
        :rtype: None
        """
        pass


class PluginManager:

    def __init__(self):
        """
        """
        self._plugins = dict()

    def plugins(self):
        """
        :rtype: dict[]
        """
        return self._plugins

    def unloadPlugins(self):
        """
        :rtype: None
        """
        for plugin in self.plugins().values():
            self.unloadPlugin(plugin)

    def unloadPlugin(self, plugin):
        """
        :type plugin: Plugin
        """
        logger.debug('Unloading plugin: %s' % plugin.path())
        plugin.unload()
        if plugin.path() in self.plugins():
            del self.plugins()[plugin.path()]

    def loadedPlugins(self):
        """
        :rtype: dict[]
        """
        return self.plugins()

    def loadPlugin(self, path, **kwargs):
        """
        :type path: str
        :type parent: QWidget || QMainWindow
        """
        logger.debug('Loading plugin: %s' % path)
        path = path.replace('\\', '/')
        if path in self.plugins():
            plugin = self.plugins().get(path)
            logger.debug("Skipping: Plugin '%s' is already loaded!" % plugin.name())
            return plugin
        if os.path.exists(path):
            dirname, basename, extension = utils.splitPath(path)
            module = imp.load_source(basename, path)
        else:
            exec 'import ' + path
            module = eval(path)
        plugin = module.Plugin(**kwargs)
        plugin.setPath(path)
        plugin.load()
        self.plugins().setdefault(path, plugin)
        return plugin