import maya.cmds as cmds
from dminutes.fx.libs import fxGeneralLib as fxgen

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

def addReleaseAttribut(node):
	
	print ('[releaseLib.addReleaseAttribut] - START') 
	
	defaultEnumList = 'default:chars:props:set:none:all'
	defaultTypeList = 'fluid:geo:instancer:particles:other'

	attr_dict = {
					0 : ['fx_type','enum',0,defaultTypeList],
					1 : ['fx_sgType','string',0],
					#2 : ['fx_lightGroup','enum',0,defaultEnumList],
					3 : ['fx_matte','enum',0,defaultEnumList],
					4 : ['fx_motionBlur','bool',1],
					5 : ['fx_emitLight','bool',0]
				}

	for key, value in attr_dict.items():
		if not cmds.attributeQuery(value[0],n=node,exists=True):
			if value[1]=='enum':
				cmds.addAttr(node,ln=value[0],nn=value[0],at=value[1],dv=value[2],en=value[3])
			elif value[1]=='string':
				cmds.addAttr(node,ln=value[0],nn=value[0],dt=value[1])
			else:
				cmds.addAttr(node,ln=value[0],nn=value[0],at=value[1],dv=value[2])
			print ('[releaseLib.addReleaseAttribut] - attr ' + value[0] + ' created') 
		else:
			print ('[releaseLib.addReleaseAttribut] - attr ' + value[0] + ' already exists') 