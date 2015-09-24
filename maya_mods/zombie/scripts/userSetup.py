

# import os, sys

# import maya.cmds as mc
#import pymel.core as pm
import pymel.mayautils

def onStartup():

	from davos_maya.tool.davossetup import DavosSetup
	DavosSetup().install()

	import stxScriptMenu
	stxScriptMenu.install()

pymel.mayautils.executeDeferred(onStartup)
