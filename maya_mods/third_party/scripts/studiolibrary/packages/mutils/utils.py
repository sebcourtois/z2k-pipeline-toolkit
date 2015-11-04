# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\utils.py
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
import mutils
import platform
try:
    import maya.mel
    import maya.cmds
except Exception as e:
    import traceback
    traceback.print_exc()

class SelectionError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class ObjectsError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class NoObjectFoundError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


class MoreThanOneObjectFoundError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)


def system():
    """
    :rtype: str
    :return: a
    """
    return platform.system().lower()


def ls(*args, **kwargs):
    """
    :rtype: list[Node]
    """
    return [ mutils.Node(name) for name in maya.cmds.ls(*args, **kwargs) or [] ]


def listAttr(node, **kwargs):
    """
    :type node: mutils.Node
    :type kwargs: {}
    :rtype: list[Attribute]
    """
    return [ mutils.Attribute(node.name(), attr) for attr in maya.cmds.listAttr(node.name(), **kwargs) or [] ]


def currentRange():
    """
    :rtype: (int, int)
    """
    start, end = selectedRange()
    if end == start:
        start, end = animationRange()
        if start == end:
            start, end = playbackRange()
    return (start, end)


def selectedRange():
    """
    :rtype: (int, int)
    """
    result = maya.mel.eval('timeControl -q -range $gPlayBackSlider')
    start, end = result.replace('"', '').split(':')
    start, end = int(start), int(end)
    if end - start == 1:
        end = start
    return (start, end)


def playbackRange():
    """
    :rtype: (int, int)
    """
    start = maya.cmds.playbackOptions(query=True, min=True)
    end = maya.cmds.playbackOptions(query=True, max=True)
    return (start, end)


def connectedAttrs(objects):
    """
    """
    result = []
    if not objects:
        raise Exception('No objects specified')
    connections = maya.cmds.listConnections(objects, connections=True, p=True, d=False, s=True) or []
    for i in range(0, len(connections), 2):
        dstObj = connections[i]
        srcObj = connections[i + 1]
        nodeType = maya.cmds.nodeType(srcObj)
        if 'animCurve' not in nodeType:
            result.append(dstObj)

    return result


def bakeConnected(objects, time, sampleBy = 1):
    """
    """
    bakeAttrs = connectedAttrs(objects)
    if bakeAttrs:
        maya.cmds.bakeResults(bakeAttrs, simulation=True, time=time, sampleBy=sampleBy, disableImplicitControl=True, preserveOutsideKeys=False, sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False, shape=False)
    else:
        print 'cannot find connection to bake!'


def animationRange(objects = None):
    """
    :rtype : (int, int)
    """
    start = 0
    end = 0
    if not objects:
        objects = maya.cmds.ls(selection=True) or []
    if objects:
        start = int(maya.cmds.findKeyframe(objects, which='first'))
        end = int(maya.cmds.findKeyframe(objects, which='last'))
    return (start, end)


def disconnectAll(name):
    """
    :type name:
    """
    for destination in maya.cmds.listConnections(name, plugs=True, source=False) or []:
        source, = maya.cmds.listConnections(destination, plugs=True)
        maya.cmds.disconnectAttr(source, destination)


def getSelectedObjects():
    """
    :rtype: list[str] @raise mutils.SelectionError:
    """
    selection = maya.cmds.ls(selection=True)
    if not selection:
        raise mutils.SelectionError('No objects selected!')
    return selection


def animCurve(fullname):
    """
    :type fullname:
    :rtype: None | str
    """
    result = None
    if maya.cmds.objExists(fullname):
        n = maya.cmds.listConnections(fullname, plugs=True, destination=False)
        if n and 'animCurve' in maya.cmds.nodeType(n):
            result = n
        elif n and 'character' in maya.cmds.nodeType(n):
            n = maya.cmds.listConnections(n, plugs=True, destination=False)
            if n and 'animCurve' in maya.cmds.nodeType(n):
                result = n
        if result:
            return result[0].split('.')[0]
    return


def deleteUnknownNodes():
    """
    """
    nodes = maya.cmds.ls(type='unknown')
    if nodes:
        for node in nodes:
            if maya.cmds.objExists(node) and maya.cmds.referenceQuery(node, inr=True):
                maya.cmds.delete(node)


def getSelectedAttrs():
    """
    :rtype: list[str]
    """
    attributes = maya.cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
    if attributes is not None:
        attributes = str(attributes)
        attributes = attributes.replace('tx', 'translateX')
        attributes = attributes.replace('ty', 'translateY')
        attributes = attributes.replace('tz', 'translateZ')
        attributes = attributes.replace('rx', 'rotateX')
        attributes = attributes.replace('ry', 'rotateY')
        attributes = attributes.replace('rz', 'rotateZ')
        attributes = eval(attributes)
    return attributes


def getNamespaceFromNames(objects):
    """
    :type objects: list[str]
    :rtype: list[str]
    """
    result = []
    for node in mutils.Node.get(objects):
        if node.namespace() not in result:
            result.append(node.namespace())

    return result


def getNamespaceFromObjects(objects):
    """
    :type objects: list[str]
    :rtype: list[str]
    """
    namespaces = [ mutils.Node(name).namespace() for name in objects ]
    return list(set(namespaces))


def getNamespaceFromSelection():
    """
    :rtype: list[str]
    """
    objects = maya.cmds.ls(selection=True)
    return getNamespaceFromObjects(objects)


def getDurationFromNodes(nodes):
    """
    :type nodes: list[str]
    :rtype: float
    """
    if nodes:
        s = maya.cmds.findKeyframe(nodes, which='first')
        l = maya.cmds.findKeyframe(nodes, which='last')
        if s == l:
            if maya.cmds.keyframe(nodes, query=True, keyframeCount=True) > 0:
                return 1
            else:
                return 0
        return l - s
    else:
        return 0


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
    return system().startswith('mac') or system().startswith('os') or system().startswith('darwin')


def isWindows():
    return system().startswith('win')


def isLinux():
    return system().startswith('lin')


def isMaya2011():
    """
    :rtype: bool
    """
    if '2011' in maya.cmds.about(version=True).replace(' ', ''):
        return True
    return False


def isMaya2012():
    """
    :rtype: bool
    """
    if '2012' in maya.cmds.about(version=True).replace(' ', ''):
        return True
    return False


def isMaya2013():
    """
    :rtype: bool
    """
    if '2013' in maya.cmds.about(version=True).replace(' ', ''):
        return True
    return False


def isMaya2014():
    """
    :rtype: bool
    """
    if '2014' in maya.cmds.about(version=True).replace(' ', ''):
        return True
    return False


def isMaya2015():
    """
    :rtype: bool
    """
    if '2015' in maya.cmds.about(version=True).replace(' ', ''):
        return True
    return False


class ScriptJob(object):
    """
    try:
        self._scriptJob = mutils.ScriptJob(e=['SelectionChanged', self.selectionChanged])
    except:
        import traceback
        traceback.print_exc()
    """

    def __init__(self, *args, **kwargs):
        self.id = maya.cmds.scriptJob(*args, **kwargs)

    def kill(self):
        if self.id:
            maya.cmds.scriptJob(kill=self.id, force=True)
            self.id = None
        return

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        if t is not None:
            self.kill()
        return