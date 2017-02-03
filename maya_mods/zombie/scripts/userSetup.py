
print "Executing Z2K Toolkit's userSetup..."

import pymel.mayautils
import pymel.core as pm

from davos_maya.tool import davossetup
davosSetup = davossetup.DavosSetup()

def onStartup():

	davosSetup.install(loadPlugins=False)

	import stxScriptMenu
	stxScriptMenu.install()

	if not pm.about(batch=True):
		for sScript in ("performStickyDeformer", "stickyDeformer", "stickyDeformerMenu"):
			pm.mel.source(sScript)

	davosSetup.loadPlugins()

pymel.mayautils.executeDeferred(onStartup)

