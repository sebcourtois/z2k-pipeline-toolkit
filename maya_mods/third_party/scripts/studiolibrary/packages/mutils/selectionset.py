# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\selectionset.py
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
import mutils
import logging
try:
    import maya.cmds
except ImportError:
    import traceback
    traceback.print_exc()

logger = logging.getLogger(__name__)

class SelectionSet(mutils.TransferBase):

    def __init__(self):
        """
        """
        mutils.TransferBase.__init__(self)
        self._namespaces = None
        return

    def namespaces(self):
        """
        :rtype: list[str]
        """
        if self._namespaces is None:
            group = mutils.groupObjects(self.objects())
            self._namespaces = group.keys()
        return self._namespaces

    def load(self, objects = None, namespaces = None, **kwargs):
        """
        :type objects:
        :type namespaces: list[str]
        :type kwargs:
        """
        validNodes = []
        dstObjects = objects
        srcObjects = self.objects()
        matches = mutils.matchObjects(srcObjects, dstObjects=dstObjects, dstNamespaces=namespaces)
        if matches:
            for srcNode, dstNode in matches:
                try:
                    if '*' in dstNode.name():
                        validNodes.append(dstNode.name())
                    else:
                        dstNode.stripFirstPipe()
                        validNodes.append(dstNode.toShortName())
                except mutils.NoObjectFoundError as msg:
                    logger.debug(msg)
                except mutils.MoreThanOneObjectFoundError as msg:
                    logger.debug(msg)

        if validNodes:
            maya.cmds.select(validNodes, **kwargs)
        else:
            raise mutils.NoMatchFoundError('No objects match when loading data')

    def select(self, objects = None, namespaces = None, **kwargs):
        """
        :type objects:
        :type namespaces: list[str]
        :type kwargs:
        """
        SelectionSet.load(self, objects=objects, namespaces=namespaces, **kwargs)

    @mutils.showWaitCursor
    def save(self, *args, **kwargs):
        """
        :type args: list[]
        :type kwargs: dict[]
        """
        self.setMetadata('mayaVersion', maya.cmds.about(v=True))
        self.setMetadata('mayaSceneFile', maya.cmds.file(q=True, sn=True))
        mutils.TransferBase.save(self, *args, **kwargs)