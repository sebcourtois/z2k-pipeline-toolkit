
print "Executing Z2K Toolkit's userSetup..."

import pymel.mayautils

def onStartup():


	import stxScriptMenu
	stxScriptMenu.install()

	from davos_maya.tool.davossetup import DavosSetup
	DavosSetup().install()

pymel.mayautils.executeDeferred(onStartup)
