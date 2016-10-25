import sys
import maya.cmds as cmds
import maya.mel as mel
from dminutes import shotconformation
reload (shotconformation)

from dminutes.fx.libs import fxGeneralLib as fxgen
from dminutes.fx.libs import fxArnoldLib as fxar
from dminutes.fx.libs import fxMeshLib as fxm
from dminutes.fx import generateCachePath as gcp
from dminutes.fx.release import releaseLib

reload(gcp)
reload(fxgen)
reload(fxar)
reload(fxm)
reload(releaseLib)


def prepare(nodes,types,variants,blurValue='0.25'):
	'''
		Prepare the FX to be released
	'''

	print ('[release.prepare] - START') 
	if fxgen.loadPlugin('SOuP.mll'):

		releaseGroups = []
		for i in range(len(nodes)):
			print i
			releaseGroup = releaseLib.createReleaseGroup(types[i],variants[i])
			releaseGroups.append(releaseGroup)

		#nodeType = findPrepareType(nodes)
		nodeType = 'mesh'

		if nodeType == 'mesh':
			outMeshes = prepareMesh(nodes,types,variants,blurValue,releaseGroups)

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

def prepareMesh(nodes,types,variants,blurValue,releaseGroups):

	print ('[release.prepareMesh] - START')
	print ('[release.prepareMesh] - nodes = ' + str(nodes))
	print ('[release.prepareMesh] - types = ' + str(types))
	print ('[release.prepareMesh] - variants = ' + str(variants))
	startFrame = str(cmds.playbackOptions(q=True,min=True)-1)
	endFrame = str(cmds.playbackOptions(q=True,max=True)+1)
	path = gcp.generatePrivateCachePath()

	fxgen.exportAlembic(nodes,startFrame,endFrame,path,types,variants,blurValue,dataFormat='ogawa')
	
	for i in range(len(nodes)):
		#newMeshes,abcNodes = fxgen.importAlembicCustom(types[i]+'_'+variants[i],path,len(nodes[i]))
		outTransforms, newMeshes, abcNodes = fxgen.importAlembicStd(types[i]+'_'+variants[i],path)
		print ('[release.prepareMesh] - newMeshes = ' + str(newMeshes))
		print ('[release.prepareMesh] - abcNodes = ' + str(abcNodes))
		print ('[release.prepareMesh] - outTransforms = ' + str(outTransforms))

		out = assignShadersToNodes(newMeshes,types[i],variants[i])
		print ('[release.prepareMesh] - out :' + str(out))
		geo_grp = cmds.listRelatives(releaseGroups[i],c=True,f=True)[0]

		for mesh in newMeshes:
			cmds.parent('|'+mesh,geo_grp)
		for mesh in out:
			cmds.parent('|'+mesh,geo_grp)

	print ('[release.prepareMesh] - END')

def assignShadersToNodes(nodes,type,variant):

	print ('[release.assignShadersToNodes] - START')
	print ('[release.assignShadersToNodes] - nodes = ' + str(nodes))
	print ('[release.assignShadersToNodes] - type = ' + str(type))
	print ('[release.assignShadersToNodes] - variant = ' + str(variant))

	outMeshLights=[]
	if len(nodes)<4:
		print 'LESS THAN 4'
		for i in range(len(nodes)):
			print(nodes[i])
			'''
				Create Base Shader with component value : R, G or B
			'''
			shadingNetwork = fxar.createArnoldShader(type+'_'+variant,'dmnToon')
			print ('[release.assignShadersToNodes] - createArnoldShader OK')
			print ('[release.assignShadersToNodes] - shadingNetwork = ' + str(shadingNetwork))
			fxar.setArnoldShaderAttr(shadingNetwork,type,str(i))
			print ('[release.assignShadersToNodes] - setArnoldShaderAttr OK')
			fxar.assignShader(shadingNetwork[0],nodes[i])
			print ('[release.assignShadersToNodes] - assignShader OK')
			fxar.arnoldMotionVectorFromMesh(nodes[i],0)
			#print ('[release.assignShadersToNodes] - arnoldMotionVectorFromMesh OK')
			
			#Create MeshLight + shader
			if type == 'lightning':
				print 'INCIDENCE'
				outMeshLight = fxar.arnoldCreateMeshLightFromMesh(nodes[i],str(i+1))
				print ('[release.assignShadersToNodes] - arnoldCreateMeshLightFromMesh OK')
				outMeshLights.append(outMeshLight)
				shadingNetwork = fxar.createArnoldShader(type+'_'+variant+'_meshLight','dmnToon')
				print ('[release.assignShadersToNodes] - createArnoldShader OK')
				print ('[release.assignShadersToNodes] - shadingNetwork = ' + str(shadingNetwork))
				
				fxar.setArnoldShaderAttr(shadingNetwork,'meshLight')
				print ('[release.assignShadersToNodes] - setArnoldShaderAttr OK')
				fxar.assignShader(shadingNetwork[0],outMeshLight)
				print ('[release.assignShadersToNodes] - assignShader OK')

	else:
		print '> 4'
		shadingNetwork1 = fxar.createArnoldShader(type+'_'+variant,'dmnToon')
		print ('[release.assignShadersToNodes] - createArnoldShader OK')
		print ('[release.assignShadersToNodes] - shadingNetwork1 = ' + str(shadingNetwork1))		
		fxar.setArnoldShaderAttr(shadingNetwork1,type,'0')
		print ('[release.assignShadersToNodes] - setArnoldShaderAttr OK')

		shadingNetwork2 = fxar.createArnoldShader(type+'_'+variant+'_meshLight','dmnToon')
		print ('[release.assignShadersToNodes] - createArnoldShader OK')
		print ('[release.assignShadersToNodes] - shadingNetwork2 = ' + str(shadingNetwork1))	
		fxar.setArnoldShaderAttr(shadingNetwork2,'meshLight')
		print ('[release.assignShadersToNodes] - setArnoldShaderAttr OK')		

		for i in range(len(nodes)):
			fxar.assignShader(shadingNetwork1[0],nodes[i])
			#fxar.arnoldMotionVectorFromMesh(nodes[i])
			if type == 'lightning':
				outMeshLight = fxar.arnoldCreateMeshLightFromMesh(nodes[i],'1')
				cmds.connectAttr(nodes[i]+'.visibility',outMeshLight+'.visibility')
				outMeshLights.append(outMeshLight)
				fxar.assignShader(shadingNetwork2[0],outMeshLight)
				fxar.arnoldMotionVectorFromMesh(nodes[i],0)
				
				
	print ('[release.assignShadersToNodes] - END')

	if outMeshLights:
		return outMeshLights
	else:
		return 1


def prepareFluid(nodes):
	print ('[release.prepareFluid] - START') 
	print ('[release.prepareFluid] - END')


def prepareParticles(nodes):
	print ('[release.prepareParticles] - START') 
	print ('[release.prepareParticles] - END')


def release(nodes):

	''' 
		release nodes
	'''
	for node in nodes:
		shotconformation.releaseShotAsset(gui = True ,toReleaseL = [node], astPrefix = "fx3", dryRun=False)