# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\mayaascii.py
"""
# Released subject to the BSD License
# Please visit http://www.voidspace.org.uk/python/license.shtml
#
# Copyright (c) 2014, Kurt Rathjen
# All rights reserved.
# Comments, suggestions and bug reports are welcome.
#
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
try:
    import maya.cmds
except Exception as e:
    import traceback
    traceback.print_exc()

class File(object):

    def __init__(self, path):
        """
        :type path: str
        """
        self.path = path

    def size(self):
        """
        File size in mb
        :rtype: float
        """
        return '%.2f' % (os.path.getsize(self.path) / 1048576.0)

    def mtime(self):
        """
        :rtype: int
        """
        return os.path.getmtime(self.path)


class Reference(File):

    def __init__(self, path, node, namespace):
        """
        :type path: str
        :type node: str
        :type namespace: str
        """
        super(Reference, self).__init__(path)
        self.path = path.replace('"', '').replace(';', '').strip()
        self.node = node.replace('"', '').strip()
        self.namespace = namespace.replace('"', '').strip()


class MayaAscii(File):

    def __init__(self, path, onlyHeader = True):
        """
        @str path: str
        """
        super(MayaAscii, self).__init__(path)
        self._lines = None
        self.minTime = None
        self.maxTime = None
        self.animationEndTime = None
        self.animationStartTime = None
        self._references = None
        self.audio = None
        self.onlyHeader = onlyHeader
        self.read()
        return

    def references(self):
        """
        :rtype: list[Reference]
        """
        return self._references

    def length(self):
        """
        :rtype: float
        """
        if self.maxTime and self.minTime:
            return self.maxTime - self.minTime
        return 0

    def read(self):
        """
        """
        self._lines = []
        self._references = []
        f = open(self.path)
        for line in f:
            if self.onlyHeader and line.startswith('createNode'):
                break
            else:
                self._lines.append(line)

        f.close()
        for l, line in enumerate(self._lines):
            if 'playbackOptions' in line:
                tokens = line.split()
                for i, token in enumerate(tokens):
                    if token == '-min':
                        self.minTime = float(tokens[i + 1])
                    if token == '-max':
                        self.maxTime = float(tokens[i + 1])
                    if token == '-ast':
                        self.animationStartTime = float(tokens[i + 1])
                    if token == '-aet':
                        self.animationEndTime = float(tokens[i + 1])

            if 'file -rdi' in line:
                tokens = line.split()
                if len(tokens) == 8:
                    self._references.append(Reference(tokens[7], tokens[6], tokens[4]))
                elif len(tokens) == 7:
                    path = self._lines[l + 1]
                    self._references.append(Reference(path, tokens[5], tokens[4]))
            if self.onlyHeader and line.startswith('createNode'):
                break

        for r in self.references():
            if r.path.endswith('.aiff'):
                self.audio = r


@mutils.timing
def test():
    path = '/test_scene.ma'
    ma = MayaAscii(path)
    print len(ma.references())


if __name__ == '__main__':
    test()