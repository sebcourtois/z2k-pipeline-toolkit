# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\snapshot.py
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
# WARNING! The following code may cause issues depending on the OS!
# It should support Maya 2009 - 2015, linux, win and mac. Its very old code.
snapshot("/tmp/snapshot_top.jpg", camera="top") 
snapshot("/tmp/snapshot_side.jpg", camera="side")    
snapshot("/tmp/snapshot_front.jpg", camera="front")
"""
import os
import platform
import logging
try:
    import maya.cmds
except ImportError as e:
    import traceback
    traceback.print_exc()

__all__ = ['SnapshotError',
 'ModelPanelNotInFocusError',
 'snapshot',
 'playblast',
 'currentModelPanel']
logger = logging.getLogger(__name__)

def isLinux():
    return platform.system().lower().startswith('lin')


class SnapshotError(Exception):
    """Base class for exceptions in this module."""
    pass


class ModelPanelNotInFocusError(Exception):
    """Base class for exceptions in this module."""
    pass


def currentModelPanel():
    """
    :rtype: str
    """
    currentPanel = maya.cmds.getPanel(withFocus=True)
    currentPanelType = maya.cmds.getPanel(typeOf=currentPanel)
    if currentPanelType in ('modelPanel',):
        return currentPanel
    raise ModelPanelNotInFocusError('Cannot find model panel with focus. Please select a model panel.')


def snapshot(path, start = None, end = None, width = 250, height = 250, step = 1, camera = None, modelPanel = None):
    """
    :type path: str
    :type start: int
    :type end: int
    :type width: int
    :type height: int
    :type step: int
    :rtype: str
    """
    if start is None:
        start = maya.cmds.currentTime(query=True)
    if end is None:
        end = start
    end = int(end)
    start = int(start)
    frame = [ i for i in range(start, end + 1, step) ]
    snapshotPanel = 'snapshotPanel'
    snapshotWindow = 'snapshotCamera'
    currentPanel = modelPanel or currentModelPanel()
    currentCamera = camera or maya.cmds.modelEditor(currentPanel, query=True, camera=True)
    if maya.cmds.window(snapshotWindow, exists=True):
        maya.cmds.deleteUI(snapshotWindow)
    if maya.cmds.modelPanel(snapshotPanel, query=True, exists=True):
        maya.cmds.deleteUI(snapshotPanel, panel=True)
    snapshotWindow = maya.cmds.window(snapshotWindow, title=snapshotWindow, sizeable=False, minimizeButton=False, maximizeButton=False)
    maya.cmds.columnLayout('columnLayout')
    maya.cmds.paneLayout(width=width + 25, height=height + 25)
    snapshotPanel = maya.cmds.modelPanel(snapshotPanel, menuBarVisible=False, camera=currentCamera)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, allObjects=False)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, grid=False)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, dynamics=False)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, activeOnly=False)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, manipulators=False)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, headsUpDisplay=False)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, selectionHiliteDisplay=False)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, polymeshes=True)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, nurbsSurfaces=True)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, subdivSurfaces=True)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, displayTextures=True)
    maya.cmds.modelEditor(snapshotPanel, camera=currentCamera, edit=True, displayAppearance='smoothShaded')
    displayLights = maya.cmds.modelEditor(currentPanel, query=True, displayLights=True)
    maya.cmds.modelEditor(snapshotPanel, edit=True, displayLights=displayLights)
    maya.cmds.setParent('columnLayout')
    maya.cmds.button(label='Take Snapshot', width=width)
    rendererName = maya.cmds.modelEditor(currentPanel, query=True, rendererName=True)
    maya.cmds.modelEditor(snapshotPanel, edit=True, rendererName=rendererName)
    maya.cmds.window(snapshotWindow, edit=True, width=width, height=height + 25)
    maya.cmds.showWindow(snapshotWindow)
    try:
        path = playblast(path, snapshotPanel, start=start, end=end, frame=frame, width=width, height=height)
    finally:
        maya.cmds.evalDeferred('import maya.cmds;\nif maya.cmds.window("%s", exists=True):\n\tmaya.cmds.deleteUI("%s", window=True)' % (snapshotWindow, snapshotWindow))

    return path


def playblast(path, modelPanel, start, end, frame, width, height):
    """
    :type path: str
    :type modelPanel: str
    :type start: int
    :type end: int
    :type width: int
    :type height: int
    :type frame: list[int]
    :rtype: str
    """
    logger.info("Playblasting '%s'" % path)
    if start == end and os.path.exists(path):
        os.remove(path)
    maya.cmds.setFocus(modelPanel or currentModelPanel())
    name, compression = os.path.splitext(path)
    path = path.replace(compression, '')
    compression = compression.replace('.', '')
    path = maya.cmds.playblast(format='image', viewer=False, percent=100, startTime=start, endTime=end, quality=100, offScreen=isLinux(), forceOverwrite=True, width=width, height=height, showOrnaments=False, compression=compression, filename=path, frame=frame)
    if not path:
        raise SnapshotError('Playblast was canceled')
    src = path.replace('####', str(int(0)).rjust(4, '0'))
    if start == end:
        dst = src.replace('.0000.', '.')
        logger.info("Renaming '%s' => '%s" % (src, dst))
        os.rename(src, dst)
        src = dst
    logger.info("Playblasted '%s'" % src)
    return src