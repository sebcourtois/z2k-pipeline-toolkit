# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\core\utils.py
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
import os
import sys
import time
import logging
import platform
import subprocess
RE_VALIDATE_PATH = re.compile('^[\\\\.:/\\sA-Za-z0-9_-]*$')
RE_VALIDATE_STRING = re.compile('^[\\sA-Za-z0-9_-]+$')

class ValidateError(Exception):
    """
    """
    pass


class Direction:
    Up = 'up'
    Down = 'down'


class SortOption:
    Name = 'name'
    Ordered = 'ordered'
    Modified = 'modified'


def system():
    """
    :rtype: str
    """
    return platform.system().lower()


def addSysPath(path):
    """
    :type path: str
    """
    if os.path.exists(path) and path not in sys.path:
        print "Adding '%s' to the sys.path" % path
        sys.path.append(path)


def validatePath(path):
    """
    :type path: str
    :raise ValidateError
    """
    if not RE_VALIDATE_PATH.match(path):
        raise ValidateError('Invalid characters in path "%s"! Please only use letters, numbers and forward slashes.' % path)


def validateString(text):
    """
    :type text: str
    :raise ValidateError
    """
    if not RE_VALIDATE_STRING.match(text):
        raise ValidateError('Invalid string "%s"! Please only use letters and numbers' % text)


def generateUniqueName(name, names, attempts = 1000):
    """
    :type name: str
    :type names: list[str]
    :type attempts: int
    :rtype: str
    """
    for i in range(1, attempts):
        result = name + str(i)
        if result not in names:
            return result

    raise Exception("Cannot generate unique name '%s'" % name)


def openLocation(path):
    """
    :type path: str
    :rtype: None
    """
    if isLinux():
        os.system('konqueror "%s"&' % path)
    elif isWindows():
        os.startfile('%s' % path)
    elif isMac():
        subprocess.call(['open', '-R', path])


def isMaya():
    """
    :rtype: bool
    """
    try:
        import maya.cmds
        maya.cmds.about(batch=True)
        return True
    except ImportError:
        return False


def isMac():
    """
    :rtype: bool
    """
    return system().startswith('mac') or system().startswith('os') or system().startswith('darwin')


def isWindows():
    """
    :rtype: bool
    """
    return system().startswith('win')


def isLinux():
    """
    :rtype: bool
    """
    return system().startswith('lin')


def user():
    """
    :rtype: str
    """
    import getpass
    return getpass.getuser().lower()


def copyPath(srcPath, dstPath):
    """
    :type srcPath: str
    :type dstPath: str
    :rtype: None
    """
    import stat
    import shutil
    if not os.path.exists(srcPath):
        raise IOError("Path doesn't exists '%s'" % srcPath)
    if os.path.isfile(srcPath):
        shutil.copyfile(srcPath, dstPath)
    elif os.path.isdir(srcPath):
        shutil.copytree(srcPath, dstPath)
    ctime = os.stat(srcPath)[stat.ST_CTIME]
    mtime = os.stat(srcPath)[stat.ST_MTIME]
    os.utime(dstPath, (ctime, mtime))


def splitPath(path):
    """
    :type path: str
    :rtype: list[str]
    """
    path = path.replace('\\', '/')
    filename, extension = os.path.splitext(path)
    return (os.path.dirname(filename), os.path.basename(filename), extension)


def listToString(data):
    """
    :type data: list[]
    :rtype: str
    """
    data = str(data).replace('[', '').replace(']', '')
    data = data.replace("'", '').replace('"', '')
    return data


def stringToList(data):
    """
    :type data: str
    :rtype: list[]
    """
    data = '["' + str(data) + '"]'
    data = data.replace(' ', '')
    data = data.replace(',', '","')
    return eval(data)


def walk(path, separator = '/', direction = Direction.Down):
    """
    :type path: str
    :type separator: str
    :type direction: Direction
    """
    if os.path.isfile(path):
        path = os.path.dirname(path)
    if not path.endswith(separator):
        path += separator
    folders = path.split(separator)
    for i, folder in enumerate(folders):
        if direction == Direction.Up:
            result = separator.join(folders[:i * -1])
        elif direction == Direction.Down:
            result = separator.join(folders[:i - 1])
        if result and os.path.exists(result):
            yield result


def listPaths(path):
    """
    :type path: str
    :rtype: list[str]
    """
    results = []
    for name in os.listdir(path):
        value = path + '/' + name
        results.append(value)

    return results


def findPaths(dirname, search, direction = Direction.Up):
    """
    :type dirname: str
    :type extension: str
    :type direction: Direction
    :rtype: dict[str]
    """
    results = []
    for path in walk(dirname, direction=direction):
        for filename in os.listdir(path):
            if search is None or search in filename:
                value = path + '/' + filename
                results.append(value)

    return results


def downloadUrl(url, destination = None):
    """
    :type url: str
    :type destination: str
    :rtype : str
    """
    try:
        if destination:
            try:
                f = open(destination, 'w')
                f.close()
            except:
                print 'Studio Library: The current user does not have permission for the directory %s' % destination
                return

        try:
            import urllib2
            f = urllib2.urlopen(url, None, 2.0)
        except Exception:
            return

        data = f.read()
        if destination:
            f = open(destination, 'wb')
            f.write(data)
            f.close()
        return data
    except:
        raise

    return


def timeAgo(t):
    """
    :type t: str
    :rtype: str
    """
    return timeDiff(t)


def timeDiff(t = False):
    """
    :type t: str
    :rtype: str
    """
    if isinstance(t, str):
        t = int(t.split('.')[0])
    from datetime import datetime
    now = datetime.now()
    if type(t) is int:
        diff = now - datetime.fromtimestamp(t)
    elif isinstance(t, datetime):
        diff = now - t
    else:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days
    if day_diff < 0:
        return ''
    if day_diff == 0:
        if second_diff < 10:
            return 'just now'
        if second_diff < 60:
            return str(second_diff) + ' seconds ago'
        if second_diff < 120:
            return 'a minute ago'
        if second_diff < 3600:
            return str(second_diff / 60) + ' minutes ago'
        if second_diff < 7200:
            return 'an hour ago'
        if second_diff < 86400:
            return str(second_diff / 3600) + ' hours ago'
    if day_diff == 1:
        return 'Yesterday'
    if day_diff < 7:
        return str(day_diff) + ' days ago'
    if day_diff < 31:
        v = day_diff / 7
        if v == 1:
            return str(v) + ' week ago'
        return str(day_diff / 7) + ' weeks ago'
    if day_diff < 365:
        v = day_diff / 30
        if v == 1:
            return str(v) + ' month ago'
        return str(v) + ' months ago'
    v = day_diff / 365
    if v == 1:
        return str(v) + ' year ago'
    return str(v) + ' years ago'