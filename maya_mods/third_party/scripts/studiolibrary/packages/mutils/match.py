# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\match.py
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
import logging
logger = logging.getLogger(__name__)

def rotateSequence(seq, current):
    """
    :type seq:
    :type current:
    :rtype:
    """
    n = len(seq)
    for i in xrange(n):
        yield seq[(i + current) % n]


def groupObjects(objects):
    """
    :type objects:
    :rtype:
    """
    results = {}
    for name in objects:
        node = mutils.Node(name)
        results.setdefault(node.namespace(), [])
        results[node.namespace()].append(name)

    return results


def indexObjects(objects):
    """
    :type objects:
    :rtype:
    """
    result = {}
    if objects:
        for name in objects:
            node = mutils.Node(name)
            result.setdefault(node.shortname(), [])
            result[node.shortname()].append(node)

    return result


def matchInIndex(node, index):
    """
    :type node: mutils.Node
    :type index: dict[list[mutils.Node]]
    :rtype: Node
    """
    result = None
    if node.shortname() in index:
        nodes = index[node.shortname()]
        if nodes:
            for n in nodes:
                if node.name().endswith(n.name()) or n.name().endswith(node.name()):
                    result = n
                    break

        if result is not None:
            index[node.shortname()].remove(result)
    return result


def matchObjects(srcObjects, dstObjects = None, dstNamespaces = None, callback = None, **kwargs):
    """
    # selection=False,
    :type srcObjects: list[str]
    :type dstObjects: list[str]
    :type dstNamespaces: list[str]
    :rtype: list[list[mutils.Node]]
    """
    results = []
    if dstObjects is None:
        dstObjects = []
    srcGroup = groupObjects(srcObjects)
    srcNamespaces = srcGroup.keys()
    if not dstObjects and not dstNamespaces:
        dstNamespaces = srcNamespaces
    if not dstNamespaces and dstObjects:
        dstGroup = groupObjects(dstObjects)
        dstNamespaces = dstGroup.keys()
    dstIndex = indexObjects(dstObjects)
    dstNamespaces2 = list(set(dstNamespaces) - set(srcNamespaces))
    dstNamespaces1 = list(set(dstNamespaces) - set(dstNamespaces2))
    usedNamespaces = []
    notUsedNamespaces = []
    for srcNamespace in srcNamespaces:
        if srcNamespace in dstNamespaces1:
            usedNamespaces.append(srcNamespace)
            for name in srcGroup[srcNamespace]:
                srcNode = mutils.Node(name)
                dstNode = mutils.Node(name)
                if dstObjects:
                    dstNode = matchInIndex(dstNode, dstIndex)
                if dstNode:
                    results.append((srcNode, dstNode))
                    if callback is not None:
                        callback(srcNode, dstNode, **kwargs)
                else:
                    logger.debug('Cannot find matching destination object for %s' % srcNode.name())

        else:
            notUsedNamespaces.append(srcNamespace)

    srcNamespaces = notUsedNamespaces
    srcNamespaces.extend(usedNamespaces)
    _index = 0
    for dstNamespace in dstNamespaces2:
        match = False
        i = _index
        for srcNamespace in rotateSequence(srcNamespaces, _index):
            if match:
                _index = i
                break
            i += 1
            for name in srcGroup[srcNamespace]:
                srcNode = mutils.Node(name)
                dstNode = mutils.Node(name)
                dstNode.setNamespace(dstNamespace)
                if dstObjects:
                    dstNode = matchInIndex(dstNode, dstIndex)
                elif dstNamespaces:
                    pass
                if dstNode:
                    match = True
                    results.append((srcNode, dstNode))
                    if callback is not None:
                        callback(srcNode, dstNode, **kwargs)
                else:
                    logger.debug('Cannot find matching destination object for %s' % srcNode.name())

    if logger.parent.level == logging.DEBUG or logger.level == logging.DEBUG:
        for dstNodes in dstIndex.values():
            for dstNode in dstNodes:
                logger.debug('Cannot find matching source object for %s' % dstNode.name())

    return results