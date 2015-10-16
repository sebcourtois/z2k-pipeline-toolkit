
print "Executing Z2K Toolkit's userSetup..."

import pymel.mayautils

def onStartup():

	from davos_maya.tool.davossetup import DavosSetup
	DavosSetup().install()

	import stxScriptMenu
	stxScriptMenu.install()

pymel.mayautils.executeDeferred(onStartup)
