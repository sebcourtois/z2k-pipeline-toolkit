

# import os, sys

# import maya.cmds as mc
import pymel.core as pm
import pymel.mayautils

def onStartup():

	import stxScriptMenu
	stxScriptMenu.install()
		
pymel.mayautils.executeDeferred( onStartup )
