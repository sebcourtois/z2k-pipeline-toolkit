import maya.cmds as cmds
import maya.mel as mel

print '[FXLIBS] - Loading Lib : fxMeshLib'

def wrapAndCombine(currentMeshs):

    dupMeshs = []
    for mesh in currentMeshs:
        dupMesh = cmds.duplicate(mesh, n=mesh + "_TMP")[0]
        transformsAttr = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility', "translate", "rotate", "scale"]
        for attr in transformsAttr:
            # ligne suivante marche pas toute seule ?!?
            cmds.setAttr(dupMesh + '.' + attr, k=True, l=False)
            # tricks mel.eval en plus de la ligne precedente pour faire marcher le unlock...c'est pas tres heureux...
            # mel.eval('CBunlockAttr "' + dupMesh + '.' + attr + '"')

        dupMeshs.append(dupMesh)
        # cmds.parent(dupMesh, root)
        # Ligne commentee car sinon les meshs se placent au centre du monde.
        # mel.eval("ResetTransformations")
        meshShape=cmds.listRelatives(mesh,s=True,f=True)[0]
        dupMeshShape = cmds.listRelatives(dupMesh,s=True,f=True)[0]
        cmds.connectAttr(meshShape + ".worldMesh", dupMeshShape + ".inMesh")
    
    if len(dupMeshs)<2:
        cmds.parent(dupMeshs[0],w=True)
        return dupMeshs[0]
    else:
        #print currentMeshs[0]
        nameSpace = currentMeshs[0].rpartition('|')[-1].rpartition(':')[0]
        #print nameSpace
        cmbMesh = cmds.polyUnite(dupMeshs, name= nameSpace + ":COMBINE")
        return cmbMesh[0]


#RETURN ALL ACTIVE SHAPES
def getActiveShape(item):
	
	shapes = cmds.listRelatives(item,s=True)
	outShapes=[]
	
	for shape in shapes:
		if not cmds.getAttr(shape+'.intermediateObject'):
			outShapes.append(shape)
			
	return outShapes

#CONNECT OUTMESH OF ITEM to a new mesh ( pCube )
def outputMesh(item):
	inMesh = cmds.polyCube(ch=0)
	outMeshShape = getActiveShape(item)[0]
	cmds.connectAttr(outMeshShape+'.outMesh',inMesh[0]+'.inMesh')
	renamed = cmds.rename(inMesh,item.split(':')[-1]+'_outMesh')
	return renamed

def envelopeMesh(mesh):

    try :
        cmds.loadPlugin('BE_OpenVDB')
        meshShape = cmds.listRelatives(mesh,s=True)[0]
        vdbFromPolygons = cmds.createNode('BE_VDBFromPolygons')
        vdbFilter = cmds.createNode('BE_VDBFilter')
        vdbConvert = cmds.createNode('BE_VDBConvertVDB')
        outMesh = cmds.polySphere(n='outEnvelope')
        cmds.delete(outMesh[1])

        cmds.setAttr(vdbFromPolygons+'.VoxelSize',.2)
        cmds.setAttr(vdbConvert+'.InvertNormal',1)
        cmds.setAttr(vdbConvert+'.ConvertTo',1)
        cmds.setAttr(vdbConvert+'.isovalue',.1)

        cmds.connectAttr(meshShape+'.worldMesh[0]',vdbFromPolygons+'.MeshInput')
        cmds.connectAttr(vdbFromPolygons+'.VdbOutput',vdbFilter+'.VdbInput')
        cmds.connectAttr(vdbFilter+'.VdbOutput',vdbConvert+'.vdbInput')
        cmds.connectAttr(vdbConvert+'.meshOutput[0]',outMesh[0]+'.inMesh')
        return outMesh
    except:
        return 0

def cleanCombine(meshes):
    """
    Combine selected meshes in one, without modifying source geometries"
    """

    polyUnite = cmds.createNode('polyUnite')
    outMesh = cmds.polySphere(n='outCombined')
    cmds.delete(outMesh[1])

    for i in range(0,len(meshes)):
        meshShape = cmds.listRelatives(meshes[i],s=True)
        if meshShape and cmds.nodeType(meshShape[0])=='mesh':
            cmds.connectAttr(meshShape[0]+'.outMesh',polyUnite+'.inputPoly['+str(i)+']')
            cmds.connectAttr(meshShape[0]+'.worldMatrix[0]',polyUnite+'.inputMat['+str(i)+']')

    cmds.connectAttr(polyUnite+'.output',outMesh[0]+'.inMesh',f=True)

    return outMesh[0]

def cleanCombine2(meshes):
    """
    Combine selected meshes in one, without modifying source geometries"
    """

    polyUnite = cmds.createNode('polyUnite')
    outMesh = cmds.polySphere(n='outCombined')
    cmds.delete(outMesh[1])

    for i in range(0,len(meshes)):
        meshShape = cmds.listRelatives(meshes[i],s=True)
        if meshShape and cmds.nodeType(meshShape[0])=='mesh':
            cmds.connectAttr(meshShape[0]+'.worldMesh[3]',polyUnite+'.inputPoly['+str(i)+']')
            cmds.connectAttr(meshShape[0]+'.worldMatrix[3]',polyUnite+'.inputMat['+str(i)+']')

    cmds.connectAttr(polyUnite+'.output',outMesh[0]+'.inMesh',f=True)

    return outMesh[0]

