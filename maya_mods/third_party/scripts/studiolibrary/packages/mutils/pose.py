# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\pose.py
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
# pose.py
import pose

# Example 1:
# Create pose from objects
p = mutils.Pose.fromObjects(objects)

# Example 2:
# Create from selected objects
objects = maya.cmds.ls(selection=True)
p = mutils.Pose.fromObjects(objects)

# Example 3:
# Save to file
path = "/tmp/pose.json"
p.save(path)

# Example 4:
# Load from file
path = "/tmp/pose.json"
p = mutils.Pose.fromPath(path)

# load to objects from file
p.load()

# load to selected objects
objects = maya.cmds.ls(selection=True)
p.load(objects=objects)

# load to namespaces
p.load(namespaces=["character1", "character2"])

# load to specified objects
p.load(objects=["Character1:Hand_L", "Character1:Finger_L"])

"""
import mutils
import logging
try:
    import maya.cmds
except ImportError:
    import traceback
    traceback.print_exc()

__all__ = ['Pose']
logger = logging.getLogger(__name__)

class Pose(mutils.SelectionSet):

    def __init__(self):
        """
        """
        mutils.SelectionSet.__init__(self)
        self._cache = None
        self._cacheKey = None
        self._isLoading = False
        self._selection = None
        self._mirrorTable = None
        self._autoKeyFrame = None
        return

    def cache(self):
        """
        :rtype: list[(Attribute, Attribute)]
        """
        return self._cache

    def createObjectData(self, name):
        """
        :type name: name
        :rtype: list[Attribute]
        """
        attrs = maya.cmds.listAttr(name, unlocked=True, keyable=True) or []
        attrs = list(set(attrs))
        attrs = [ mutils.Attribute(name, attr) for attr in attrs ]
        result = {'attrs': self.attrs(name)}
        for attr in attrs:
            if attr.isValid():
                if attr.value() is None:
                    logger.warning('Cannot save the attribute %s with value None.' % attr.fullname())
                else:
                    result['attrs'][attr.attr()] = {'type': attr.type(),
                     'value': attr.value()}

        return result

    def attrs(self, name):
        """
        :type name: str
        :rtype: dict[]
        """
        return self.object(name).get('attrs', {})

    def attr(self, name, attr):
        """
        :type name: str
        :rtype: dict[]
        """
        return self.attrs(name).get(attr, {})

    def attrType(self, name, attr):
        """
        :type name: str
        :type attr: str
        :rtype: str
        """
        return self.attr(name, attr).get('type', None)

    def attrValue(self, name, attr):
        """
        :type name: str
        :type attr: str
        :rtype: str | int | float
        """
        return self.attr(name, attr).get('value', None)

    def beforeLoad(self, clearSelection = True):
        """
        :type clearSelection: bool
        """
        logger.debug("Open Load '%s'" % self.path())
        if self._isLoading:
            return
        self._isLoading = True
        maya.cmds.undoInfo(openChunk=True)
        self._selection = maya.cmds.ls(selection=True) or []
        self._autoKeyFrame = maya.cmds.autoKeyframe(query=True, state=True)
        maya.cmds.autoKeyframe(edit=True, state=False)
        maya.cmds.select(clear=clearSelection)

    def afterLoad(self):
        """
        :rtype: None
        """
        if not self._isLoading:
            return
        else:
            self._isLoading = False
            if self._selection:
                maya.cmds.select(self._selection)
                self._selection = None
            maya.cmds.autoKeyframe(edit=True, state=self._autoKeyFrame)
            maya.cmds.undoInfo(closeChunk=True)
            logger.debug("Close Load '%s'" % self.path())
            return

    @mutils.timing
    def load(self, objects = None, namespaces = None, attrs = None, blend = 100, key = False, refresh = False, ignoreConnected = False, onlyConnected = False, cache = True, mirrorTable = None, mirror = False, clearSelection = False, batchMode = False):
        """
        :type objects: list[str]
        :type namespaces: list[str]
        :type attrs: list[str]
        :type blend: float
        :type key: bool
        :type refresh: bool
        :type mirrorTable: mutils.MirrorTable
        """
        if mirror and not mirrorTable:
            logger.warning('Cannot mirror pose without a mirror table!')
            mirror = False
        if batchMode:
            key = False
        self.updateCache(objects=objects, namespaces=namespaces, dstAttrs=attrs, ignoreConnected=ignoreConnected, onlyConnected=onlyConnected, cache=cache, mirrorTable=mirrorTable)
        self.beforeLoad(clearSelection=clearSelection)
        try:
            self.loadCache(blend=blend, key=key, mirror=mirror)
        finally:
            if not batchMode:
                self.afterLoad()

        if refresh:
            maya.cmds.refresh(cv=True)

    def updateCache(self, objects = None, namespaces = None, dstAttrs = None, ignoreConnected = False, onlyConnected = False, cache = True, mirrorTable = None):
        """
        :type objects: list[str]
        :type namespaces: list[str]
        :type dstAttrs: list[str]
        """
        cacheKey = str(objects) + str(namespaces) + str(dstAttrs) + str(ignoreConnected) + str(maya.cmds.currentTime(query=True))
        if self._cacheKey != cacheKey or not cache:
            self._cache = []
            self._cacheKey = cacheKey
            dstObjects = objects
            srcObjects = self.objects()
            usingNamespaces = not objects and namespaces
            if mirrorTable:
                self.setMirrorTable(mirrorTable)
            mutils.matchObjects(srcObjects, dstObjects=dstObjects, dstNamespaces=namespaces, callback=self.cacheNode, dstAttrs=dstAttrs, ignoreConnected=ignoreConnected, onlyConnected=onlyConnected, usingNamespaces=usingNamespaces)
        if not self.cache():
            raise mutils.NoMatchFoundError('No objects match when loading data')

    def setMirrorAxis(self, name, mirrorAxis):
        """
        :type name: str
        :type mirrorAxis: list[int]
        """
        if name in self.objects():
            self.object(name).setdefault('mirrorAxis', mirrorAxis)
        else:
            logger.debug('Object does not exist in pose. Cannot set mirror axis for %s' % name)

    def mirrorAxis(self, name):
        """
        :rtype: list[int] | None
        """
        result = None
        if name in self.objects():
            result = self.object(name).get('mirrorAxis', None)
        if result is None:
            logger.debug('Cannot find mirror axis in pose for %s' % name)
        return result

    def mirrorTable(self):
        """
        :rtype: mutils.MirrorTable
        """
        return self._mirrorTable

    def setMirrorTable(self, mirrorTable):
        """
        :type mirrorTable: mutils.MirrorTable
        """
        self._mirrorTable = mirrorTable
        mirrorTable.matchObjects(objects=self.objects().keys(), callback=self.updateMirrorAxis)

    def updateMirrorAxis(self, srcNode, dstNode, mirrorAxis):
        """
        :type srcNode: mutils.Node
        :type mirrorAxis: list[int]
        """
        self.setMirrorAxis(dstNode, mirrorAxis)

    def cacheNode(self, srcNode, dstNode, dstAttrs = None, ignoreConnected = None, onlyConnected = None, usingNamespaces = None):
        """
        :type srcNode: mutils.Node
        :type dstNode: mutils.Node
        """
        mirrorAxis = None
        mirrorObject = None
        dstNode.stripFirstPipe()
        if self.mirrorTable():
            mirrorObject = self.mirrorTable().mirrorObject(srcNode.name())
            if not mirrorObject:
                mirrorObject = srcNode.name()
                logger.debug('Cannot find mirror object in pose for %s' % srcNode.name())
            mirrorAxis = self.mirrorAxis(mirrorObject) or self.mirrorAxis(srcNode.name())
            if mirrorObject and not maya.cmds.objExists(mirrorObject):
                logger.debug('Mirror object does not exist in the scene %s' % mirrorObject)
        if usingNamespaces:
            try:
                dstNode = dstNode.toShortName()
            except mutils.NoObjectFoundError as msg:
                logger.debug(msg)
                return
            except mutils.MoreThanOneObjectFoundError as msg:
                logger.debug(msg)
                return

        for attr in self.attrs(srcNode.name()):
            if dstAttrs and attr not in dstAttrs:
                continue
            dstAttribute = mutils.Attribute(dstNode.name(), attr)
            isConnected = dstAttribute.isConnected()
            if ignoreConnected and isConnected or onlyConnected and not isConnected:
                continue
            type_ = self.attrType(srcNode.name(), attr)
            value = self.attrValue(srcNode.name(), attr)
            srcMirrorValue = self.attrMirrorValue(mirrorObject, attr, mirrorAxis=mirrorAxis)
            srcAttribute = mutils.Attribute(dstNode.name(), attr, value=value, type=type_)
            dstAttribute.update()
            self._cache.append((srcAttribute, dstAttribute, srcMirrorValue))

        return

    def attrMirrorValue(self, name, attr, mirrorAxis):
        """
        :type name: str
        :type attr: str
        :type mirrorAxis: list[]
        :rtype: None | int | float
        """
        value = None
        if self.mirrorTable() and name:
            value = self.attrValue(name, attr)
            if value is not None:
                value = self.mirrorTable().formatValue(attr, value, mirrorAxis)
            else:
                logger.debug('cannot find mirror value for %s.%s' % (name, attr))
        return value

    def loadCache(self, blend = 100, key = False, mirror = False):
        """
        :type blend: float
        :type key: bool
        """
        cache = self.cache()
        for i in range(0, len(cache)):
            srcAttribute, dstAttribute, srcMirrorValue = cache[i]
            if srcAttribute and dstAttribute:
                if mirror and srcMirrorValue is not None:
                    value = srcMirrorValue
                else:
                    value = srcAttribute.value()
                try:
                    dstAttribute.set(value, blend=blend, key=key)
                except (ValueError, RuntimeError):
                    cache[i] = (None, None)
                    logger.debug('Ignoring %s.' % dstAttribute.fullname())

        return