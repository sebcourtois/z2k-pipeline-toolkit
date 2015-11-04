# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\__init__.py
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
from core.gui import *
from core.utils import *
from core.package import *
from core.tempdir import *
from core.basepath import *
from core.resource import *
from core.metafile import *
from core.settings import *
from core.analytics import *
from core.shortuuid import *
from core.decorators import *
from core.masterpath import *
from core.pluginmanager import *
__version__ = '1.8.6'
_scriptJob = None
_application = None

def dirname():
    """
    :rtype: str
    """
    encoding = sys.getfilesystemencoding()
    return os.path.dirname(unicode(os.path.abspath(__file__), encoding)).replace('\\', '/')


CHECK_FOR_UPDATES_ENABLED = True
PACKAGES_DIRNAME = dirname() + '/packages'
RESOURCE_DIRNAME = dirname() + '/gui/resource'
PACKAGE_HELP_URL = 'http://www.studiolibrary.com'
PACKAGE_JSON_URL = 'http://dl.dropbox.com/u/28655980/studiolibrary/studiolibrary.json'
Resource.DEFAULT_DIRNAME = RESOURCE_DIRNAME
addSysPath(PACKAGES_DIRNAME)
from gui import *
from api.folder import *
from api.record import *
from api.record import *
from api.plugin import *
from api.library import *
from gui.librariesmenu import *
from gui.statuswidget import *
from gui.librarywidget import *
from gui.folderswidget import *
from gui.recordswidget import *
from gui.settingsdialog import *
from gui.imagesequencetimer import *
import config

def main(name = None, path = None, plugins = None, show = True, analytics = True, root = None, **kwargs):
    """
    :type name: str
    :type path: str
    :type plugins: list[str]
    :type show: bool
    :type analytics: bool
    :type root: bool
    :type kwargs: dict[]
    :rtype: studiolibrary.Library
    """
    import studiolibrary
    studiolibrary.analytics().setEnabled(analytics)
    if not name:
        library = studiolibrary.Library.default()
    else:
        library = studiolibrary.Library.fromName(name)
    if plugins is None:
        library.setPlugins(Library.DEFAULT_PLUGINS)
    else:
        library.setPlugins(plugins)
    if root:
        path = root
    if path:
        library.setPath(path)
    isAppRunning = bool(QtGui.QApplication.instance())
    if not isAppRunning:
        studiolibrary._application = QtGui.QApplication(sys.argv)
    if studiolibrary.isMaya():
        import maya.cmds
        if not studiolibrary._scriptJob:
            studiolibrary._scriptJob = maya.cmds.scriptJob(event=['quitApplication', 'import studiolibrary;\nfor window in studiolibrary.windows():\n\twindow.saveSettings()'])
    if show:
        library.show(**kwargs)
    if not isAppRunning:
        sys.exit(studiolibrary._application.exec_())
    return library


_package = Package()

def package():
    """
    :rtype: package.Package
    """
    _package.setJsonUrl(PACKAGE_JSON_URL)
    _package.setHelpUrl(PACKAGE_HELP_URL)
    _package.setVersion(__version__)
    return _package


def version():
    """
    :rtype: str
    """
    return package().version()


_analytics = Analytics(tid=Analytics.DEFAULT_ID, name='StudioLibrary', version=package().version())

def analytics():
    """
    :rtype: analytics.Analytics
    """
    _analytics.setId(studiolibrary.Analytics.DEFAULT_ID)
    _analytics.setEnabled(studiolibrary.Analytics.ENABLED)
    return _analytics


def application():
    """
    :rtype: QtCore.QApplication
    """
    return _application


def windows():
    """
    :rtype: list[MainWindow]
    """
    return Library.windows()


def library(name = None):
    """
    :rtype: studiolibrary.Library
    """
    return Library.fromName(name)


def libraries():
    """
    :rtype: list[studiolibrary.Library]
    """
    return Library.libraries()


def loadFromCommand():
    """
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-p', '--plugins', dest='plugins', help='', metavar='PLUGINS', default='None')
    parser.add_option('-r', '--root', dest='root', help='', metavar='ROOT')
    parser.add_option('-n', '--name', dest='name', help='', metavar='NAME')
    parser.add_option('-v', '--version', dest='version', help='', metavar='VERSION')
    options, args = parser.parse_args()
    name = options.name
    plugins = eval(options.plugins)
    main(name=name, plugins=plugins)


if __name__ == '__main__':
    loadFromCommand()
else:
    print '\n-------------------------------\nStudio Library is a free python script for managing poses and animation in Maya.\nComments, suggestions and bug reports are welcome.\n\nVersion: %s\n\nwww.studiolibrary.com\nkurt.rathjen@gmail.com\n--------------------------------\n' % package().version()