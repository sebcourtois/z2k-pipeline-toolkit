

import os, sys

import pymel.mayautils

def onStartup():

	if os.path.normcase(sys.executable).endswith("maya.exe") or os.path.normcase(sys.executable).endswith("Maya"):

		import stxScriptMenu
		stxScriptMenu.install()

	from davos_maya.tool.davossetup import DavosSetup
	DavosSetup().install()

pymel.mayautils.executeDeferred(onStartup)
