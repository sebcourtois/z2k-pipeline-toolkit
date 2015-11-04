# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\tests\test_base.py
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
   # objects of its contributors may be used to endorse or promote products
   # derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY KURT RATHJEN  ''AS IS'' AND ANY
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
import math
import mutils
import unittest
import maya.cmds
TEST_DATA_DIR = os.path.join(os.path.dirname(mutils.__file__), 'tests', 'data')

class TestBase(unittest.TestCase):

    def __init__(self, *args):
        """
        @param args:
        """
        unittest.TestCase.__init__(self, *args)
        self.srcPath = os.path.join(TEST_DATA_DIR, 'test_pose.ma')
        self.dstPath = os.path.join(TEST_DATA_DIR, 'test_pose.pose')
        self.srcObjects = ['srcSphere:lockedNode', 'srcSphere:offset', 'srcSphere:sphere']
        self.dstObjects = ['dstSphere:lockedNode', 'dstSphere:offset', 'dstSphere:sphere']
        self.srcNamespaces = ['srcSphere']
        self.dstNamespaces = ['dstSphere']

    def dataDir(self):
        return os.path.join(os.path.dirname(mutils.__file__), 'tests', 'data')

    def open(self, path = None):
        """
        """
        if path is None:
            path = self.srcPath
        maya.cmds.file(self.srcPath, open=True, force=True, executeScriptNodes=False, ignoreVersion=True)
        return

    def listAttr(self, srcObjects = None, dstObjects = None):
        """
        :rtype: list[mutils.Attribute]
        """
        results = []
        srcObjects = srcObjects or self.srcObjects
        dstObjects = dstObjects or self.dstObjects
        for i, srcObj in enumerate(srcObjects):
            srcObj = srcObjects[i]
            dstObj = dstObjects[i]
            for srcAttr in maya.cmds.listAttr(srcObj, k=True, unlocked=True, scalar=True) or []:
                srcAttribute = mutils.Attribute(srcObj, srcAttr)
                dstAttribute = mutils.Attribute(dstObj, srcAttr)
                results.append((srcAttribute, dstAttribute))

        return results