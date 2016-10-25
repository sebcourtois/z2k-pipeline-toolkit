import maya.cmds as cmds
print '[FXLIBS] - Loading Lib : releaseLib'

def createReleaseGroup(type,variant):
	'''
		create standard release group
	'''
	fx3 = cmds.group(em=True,n='fx3_'+type+'_'+variant)
	geo = cmds.group(em=True,n='geo_grp')

	cmds.parent(geo,fx3)
	#cmds.parent(fx3,fxGroup)

	return fx3

def addAttributToGroup(group):
	print ('[releaseLib.addAttributToGroup] - START') 
	print ('[releaseLib.addAttributToGroup] - END')