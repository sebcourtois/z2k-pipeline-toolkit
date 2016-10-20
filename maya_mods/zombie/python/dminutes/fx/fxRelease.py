import sys
import maya.cmds as cmds
import maya.mel as mel
from dminutes import shotconformation
reload (shotconformation)

from dminutes.fx.libs import fxGeneralLib as fxgal
from dminutes.fx.libs import fxRenderLib as fxrnd
from dminutes.fx.libs import fxMeshLib as fxm
from dminyes.fx import generateCachePath as gcp

reload(gcp)
reload(fxgal)
reload(fxrnd)
reload(fxm)


def releaseGroup(type,variant):
	'''
		create standard release group
	'''
	fx3 = cmds.group(em=True,n='fx3_'+type+'_'+variant)
	geo = cmds.group(em=True,n='geo_grp')

	cmds.parent(geo,fx3)
	#cmds.parent(fx3,fxGroup)

	return fx3

def releasePrepare(nodes,type,variant,blurValue='0.25'):
	'''
		Prepare the release of nodes
		TODO : if mode than 3 nodes = WARNING for R - G - B
	'''
	if fxgal.loadPlugin('SOuP.mll'):

		startFrame = str(cmds.playbackOptions(q=True,min=True)-1)
		endFrame = str(cmds.playbackOptions(q=True,max=True)+1)

		if len(nodes)<4:
			if type=='lightning':

				path = gcp.generatePrivateCachePath()

				outNodes=[]
				for i in range(len(nodes)):

					subName = type+'_'+variant+str(i+1)
					print('[fxRelease.releasePrepare] - subName = ' + subName)

					outPath = fxgal.exportAlembic([nodes[i]],startFrame,endFrame,path,subName,blurValue,dataFormat='ogawa')
					outMeshes, outAbcs, outTransforms = list(fxgal.importAlembicStd(path,subName))

					for outTransform in outTransforms:
						cmds.select(outTransform,hi=True)
						sel = cmds.ls(sl=True,l=True)
						for item in sel:
							if cmds.nodeType(item) == 'transform' and not cmds.listRelatives(item,c=True,f=True):
								cmds.delete(item)
							elif cmds.nodeType(item) == 'transform' and cmds.listRelatives(item,s=True,f=True) and cmds.nodeType(cmds.listRelatives(item,s=True,f=True)[0]) == 'mesh':
								outMeshes.append(item)
				
					print('[fxRelease.releasePrepare] - outMeshes = ' + str(outMeshes))

					shader1 = fxrnd.createArnoldShader('dmnToon',type)
					cmds.setAttr(shader1[2]+'.color',0,0,0,type='double3')
					cmds.setAttr(shader1[2]+'.incandescence',1,.3,.3,type='double3')
					value=[0,0,0]
					value[i]=1

					cmds.setAttr(shader1[1]+'.ambientColor',value[0],value[1],value[2],type='double3')
					cmds.setAttr(shader1[1]+'.ambientTint',value[0],value[1],value[2],type='double3')
					cmds.setAttr(shader1[1]+'.ambientIntensity',1)

					shader2 = fxrnd.createArnoldShader('dmnToon',type)
					cmds.setAttr(shader2[2]+'.color',0,0,0,type='double3')
					cmds.setAttr(shader2[2]+'.incandescence',1,1,0,type='double3')

					for mesh in outMeshes:
						cmds.setAttr(mesh+'.castsShadows',0)
						fxrnd.arnoldMotionVectorFromMesh(mesh,0)
						fxrnd.assignShader(shader1[0],mesh)
						incidenceParent = fxrnd.arnoldCreateMeshLight(mesh,i)
						fxrnd.assignShader(shader2[0],incidenceParent)
					
						outNodes.extend([mesh,incidenceParent])

					if outTransforms:
						outNodes = [outTransforms[0]]
					print('[fxRelease.releasePrepare] - outNodes for ' + nodes[i] + ' = ' + str(outNodes))

				fx3 = releaseGroup(type,variant)
				print('[fxRelease.releasePrepare] - fx3 = ' + str(fx3))

				childs = cmds.listRelatives(fx3,c=True,ad=True,f=True)
				cmds.parent(outNodes,[child for child in childs if 'geo_grp' in child])
		else:
			message = 'warning("[fxRelease.releasePrepare] - More than 3 nodes selected - canceled")'
			mel.eval(message)


def redirectAlembicPath(abcNode):

	'''
		redirect alembic Path 
	'''
	filePath = cmds.getAttr(abcNode+'.abc_File')
	if not '$ZOMB_SHOT_PATH' in filePath:
		newFilePath = '$ZOMB_SHOT_PATH/' + filePath.split('shot/')[1]
		cmds.setAttr(abcNode+'.abc_File',newFilePath,type='string')
		print ('[redirectAlembicPath] - path for node ' + abcNode + ' correctly redirected')
		return newFilePath
	else:
		print ('[redirectAlembicPath] - node ' + abcNode + ' is already redirected - skipped')


def release(nodes):

	''' 
		release nodes
	'''
	for node in nodes:
		shotconformation.releaseShotAsset(gui = True ,toReleaseL = [node], astPrefix = "fx3", dryRun=False)