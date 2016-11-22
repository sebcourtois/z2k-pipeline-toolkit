import sys
import maya.cmds as cmds
import maya.mel as mel
from dminutes import shotconformation
reload (shotconformation)

from dminutes.fx.libs import fxGeneralLib as fxgen
from dminutes.fx.libs import fxArnoldLib as fxar
from dminutes.fx import generateCachePath as gcp
from dminutes.fx.release import releaseLib

reload(gcp)
reload(fxgen)
reload(fxar)
reload(releaseLib)


def prepare(nodes,types,variants,blurOffset='0'):
	'''
		Prepare the FX to be released
	'''

	print ('[release.prepare] - START') 
	if fxgen.loadPlugin('SOuP.mll'):

		releaseGroups = []
		MLGroup = ''
		for i in range(len(nodes)):
			releaseGroup = releaseLib.createReleaseGroup(types[i],variants[i])
			releaseGroups.append(releaseGroup)

		if 'lightning' in types:
			MLGroup = releaseLib.createReleaseGroup('lightning','meshLights')

		#nodeType = findPrepareType(nodes)
		nodeType = 'mesh'

		if nodeType == 'mesh':
			outMeshes = prepareMesh(nodes,types,variants,blurOffset,releaseGroups,MLGroup)

		if nodeType == 'fluid':
			outFluids = prepareFluid(nodes)

		if nodeType == 'particles':
			outParticles = prepareParticles(nodes)

		print ('[release.prepare] - END') 
		return 1


def findPrepareType(nodes):
	'''
		Look at what is inside the provided nodes 
	'''

	print ('[release.findPrepareType] - START') 

	for node in nodes:
		nodeType = cmds.nodeType(node)
		shape = cmds.listRelatives(node,s=True)

		if shape and nodeType == 'transform' and cmds.nodeType(shape[0]) == 'mesh':
			print ('[release.findPrepareType] - found mesh :' + node)
		elif shape and nodeType == 'transform' and cmds.nodeType(shape[0]) == 'fluidShape':
			print ('[release.findPrepareType] - found fluid :' + node)
		elif shape and nodeType == 'transform' and cmds.nodeType(shape[0]) == 'nParticle':
			print ('[release.findPrepareType] - found particles :' + node)
		elif not shape and nodeType == 'transform':
			print ('[release.findPrepareType] - found transform :' + node)

		else:
			print nodeType
	print ('[release.findPrepareType] - END') 


def prepareMesh(nodes,types,variants,blurOffset,releaseGroups,MLGroup):

	print ('[release.prepareMesh] - START')
	print ('[release.prepareMesh] - nodes = ' + str(nodes))
	print ('[release.prepareMesh] - types = ' + str(types))
	print ('[release.prepareMesh] - variants = ' + str(variants))
	startFrame = str(cmds.playbackOptions(q=True,min=True)-1)
	endFrame = str(cmds.playbackOptions(q=True,max=True)+1)
	path = gcp.generatePrivateCachePath()

	fxgen.exportAlembic(nodes,startFrame,endFrame,path,types,variants,blurOffset,dataFormat='ogawa')

	ml_grp = cmds.listRelatives(MLGroup,c=True,f=True)[0]

	for i in range(len(nodes)):
		geo_grp = cmds.listRelatives(releaseGroups[i],c=True,f=True)[0]
		#newMeshes,abcNodes = fxgen.importAlembicCustom(types[i]+'_'+variants[i],path,len(nodes[i]))
		outTransforms, newMeshes, abcNodes = fxgen.importAlembicStd(types[i]+'_'+variants[i],path)

		print ('[release.prepareMesh] - newMeshes = ' + str(newMeshes))
		print ('[release.prepareMesh] - abcNodes = ' + str(abcNodes))
		print ('[release.prepareMesh] - outTransforms = ' + str(outTransforms))

		out = assignShadersToNodes(newMeshes,types[i],variants[i])
		print ('[release.prepareMesh] - out :' + str(out))

		if blurOffset != 0:
			for mesh in newMeshes:
				fxar.arnoldMotionVectorFromMesh(mesh,0)
				print ('[release.prepareMesh] - arnoldMotionVectorFromMesh OK')
				cmds.parent('|'+mesh,geo_grp)

		if types[i]=='lightning':
			outTransformsML, newMeshesML, abcNodesML = fxgen.importAlembicStd(types[i]+'_'+variants[i],path)
			print ('[release.prepareMesh] - newMeshesML = ' + str(newMeshes))
			print ('[release.prepareMesh] - abcNodesML = ' + str(abcNodes))
			print ('[release.prepareMesh] - outTransformsML = ' + str(outTransforms))
			assignShadersToNodes(newMeshesML,'meshLight',variants[i])

			for i in range(len(newMeshesML)):
				mesh = cmds.rename(newMeshesML[i],newMeshesML[i]+'meshLight')
				fxar.setMeshLightFromMesh(mesh,str((i+1)%6))
				print ('[release.prepareMesh] - arnoldCreateMeshLightFromMesh OK')
				cmds.parent('|'+mesh,ml_grp)		

	print ('[release.prepareMesh] - END')

def assignShadersToNodes(nodes,type,variant):

	print ('[release.assignShadersToNodes] - START')
	print ('[release.assignShadersToNodes] - nodes = ' + str(nodes))
	print ('[release.assignShadersToNodes] - type = ' + str(type))
	print ('[release.assignShadersToNodes] - variant = ' + str(variant))

	shadingNetworks =  []

	if type != 'meshLight':
		for i in range(len(nodes)):
			'''
				Create Base Shader with component value : R, G or B
			'''
			print i
			print (i)%10
			shadingNetwork = fxar.createArnoldShader(type+'_'+variant,'dmnToon')
			print ('[release.assignShadersToNodes] - shadingNetwork = ' + str(shadingNetwork))
			fxar.setArnoldShaderAttr(shadingNetwork,type,str(i%10))
			print ('[release.assignShadersToNodes] - setArnoldShaderAttr OK')
			fxar.assignShader(shadingNetwork[0],nodes[i])
			print ('[release.assignShadersToNodes] - assignShader OK')
			shadingNetworks.append(shadingNetwork)

	elif type == 'meshLight':

			shadingNetwork = fxar.createArnoldShader(type+'_'+variant+'_meshLight','dmnToon')
			print ('[release.assignShadersToNodes] - createArnoldShader OK')
			print ('[release.assignShadersToNodes] - shadingNetwork = ' + str(shadingNetwork))

			fxar.setArnoldShaderAttr(shadingNetwork,'meshLight')
			print ('[release.assignShadersToNodes] - setArnoldShaderAttr OK')

			for i in range(len(nodes)):
				fxar.assignShader(shadingNetwork[0],nodes[i])
				print ('[release.assignShadersToNodes] - assignShader OK')
				shadingNetworks.append(shadingNetwork)
				print ('[release.assignShadersToNodes] - assignShader OK')
				
	print ('[release.assignShadersToNodes] - END')

	return shadingNetworks


def prepareFluid(nodes):
	print ('[release.prepareFluid] - START')
	'''
	'''
	print ('[release.prepareFluid] - END')


def prepareParticles(nodes):
	print ('[release.prepareParticles] - START') 
	print ('[release.prepareParticles] - END')


def release(nodes):

	'''
		Release les nodes
	'''
	from davos_maya.tool.publishing import lockSceneDependenciesToCurrentVersion
	lockSceneDependenciesToCurrentVersion()
	for node in nodes:
		shotconformation.releaseShotAsset(gui = True ,toReleaseL = [node], astPrefix = "fx3", dryRun=False)