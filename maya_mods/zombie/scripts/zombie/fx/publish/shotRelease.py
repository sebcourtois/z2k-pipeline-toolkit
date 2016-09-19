import maya.cmds as cmds
from dminutes import shotconformation
reload (shotconformation)

def releaseSelected(nodes)
shotconformation.releaseShotAsset(gui = True ,toReleaseL = nodes, astPrefix = "fx3", dryRun=False)

def releaseInit():
	if not cmds.objExists('fx'):
		fxGroup = cmds.group(em=True,n='fx')
	else:
		fxGroup = '|fx'

	fx3 = cmds.group(em=True,n='fx3_type_variant')
	asset = cmds.group(em=True,n='asset')
	geo = cmds.group(em=True,n='geo_grp')

	cmds.parent(geo,asset)
	cmds.parent(asset,fx3)
	cmds.parent(fx3,fxGroup)

	return fx3