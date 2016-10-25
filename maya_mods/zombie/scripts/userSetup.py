
print "Executing Z2K Toolkit's userSetup..."

import pymel.mayautils
import pymel.core as pm

def onStartup():

	from davos_maya.tool.davossetup import DavosSetup
	DavosSetup().install()

	import stxScriptMenu
	stxScriptMenu.install()

	if not pm.about(batch=True):
		for sScript in ("performStickyDeformer", "stickyDeformer", "stickyDeformerMenu"):
			pm.mel.source(sScript)

	pm.loadPlugin("xgenToolkit.mll")
	pm.mel.xgmPreRendering()

pymel.mayautils.executeDeferred(onStartup)


