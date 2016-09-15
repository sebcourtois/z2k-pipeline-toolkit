
print "Executing Z2K Toolkit's userSetup..."

import pymel.mayautils
import pymel.core as pm

def onStartup():

	from davos_maya.tool.davossetup import DavosSetup
	DavosSetup().install()

	import stxScriptMenu
	stxScriptMenu.install()

	for sScript in ("performStickyDeformer", "stickyDeformer", "stickyDeformerMenu"):
		pm.mel.source(sScript)

pymel.mayautils.executeDeferred(onStartup)


