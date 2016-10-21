import maya.cmds as cmds
import maya.mel as mel
import fxMainLib as fxm

def createNParticlesAndEmitter():
	cmds.select(cl=True)
	emitter = cmds.emitter()
	nParticles = cmds.nParticle()
	cmds.connectDynamic(nParticles[0],em=emitter)
	nucleus = getConnectedNucleus(nParticles[0])
	print('[CREATENPARTICLESANDEMITTER] - following nodes created and connected : ' + emitter[0] + ' ' + nParticles[1] + ' ' + str(nucleus))
	return [emitter[0],nParticles[0],nucleus]
	
def getConnectedNucleus(nParticle):
	print nParticle
	shape = cmds.listRelatives(nParticle,s=True)[0]
	nucleus = cmds.listConnections(shape+'.startFrame',s=True)
	return nucleus
	
def traceParticles(item):

	if not cmds.pluginInfo('SOuP',q=True,l=True):
		mel.eval('error("[TRACEPARTICLES] - SOuP plugin not found or not loaded - cannot trace"')
	else:
		outNodes = createNParticlesAndEmitter()
		print outNodes
		
		command = 'python("soup().create(\'pointAttributeToArray\')")'
		pointAttributeToArray = mel.eval(command)
		print pointAttributeToArray
		
		command = 'python("soup().create(\'pointCloudToCurve\')")'
		pointCloudToCurve = mel.eval(command)
		print pointCloudToCurve
		
		circle = cmds.circle(ch=0,n='fxTrace')
		print circle
		
		cmds.connectAttr(outNodes[1]+'.worldPosition',pointAttributeToArray+'.inGeometry')
		cmds.connectAttr(outNodes[1]+'.idIndex',pointAttributeToArray+'.inComponents')
		cmds.connectAttr(pointAttributeToArray+'.outPositionPP',pointCloudToCurve[0]+'.inArray')
		cmds.connectAttr(pointCloudToCurve[0]+'.outCurve',circle[0]+'.create')
		
		cmds.setAttr(pointAttributeToArray+'.useComponents',1)
		cmds.setAttr(pointAttributeToArray+'.pointPosition',1)
		
		cmds.parentConstraint(item,outNodes[0])
		
		fxGroup = fxm.fxGlobalSetup()
		
		cmds.parent(outNodes[0],fxGroup)
		cmds.parent(outNodes[1],fxGroup)
		cmds.parent(outNodes[2],fxGroup)
		cmds.parent(circle,fxGroup)

def getAllnParticles():
	particles = cmds.ls(type='nParticle')
	return particles

def getCacheNode(nParticle):
	shape = cmds.listRelatives(nParticle,s=True)[0]
	cacheNode = cmds.listConnections(shape+'.playFromCache',s=True)
	if cacheNode:
		return cacheNode
	else:
		return 0