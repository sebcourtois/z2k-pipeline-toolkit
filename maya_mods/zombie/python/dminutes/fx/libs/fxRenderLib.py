import maya.cmds as cmds
import maya.mel as mel
import os

print '[FXLIBS] - Loading Lib : fxRenderLib'

def createArnoldShader(type,shaderName):

    mat = cmds.createNode('dmnToon',n='mat_'+shaderName+'_dmnToon')
    print('[fxRenderLib.createArnoldShader] - material = ' + mat)
    lambert = cmds.createNode('lambert',n='pre_'+shaderName+'_lambert')
    print('[fxRenderLib.createArnoldShader] - lambert = ' + lambert)
    cmds.select(cl=True)
    sgr= cmds.sets(n='sgr_'+shaderName,nss=True,r=True)
    print('[fxRenderLib.createArnoldShader] - shading engine = ' + sgr)

    cmds.connectAttr(mat+'.outColor',sgr+'.aiSurfaceShader')
    cmds.connectAttr(lambert+'.outColor',sgr+'.surfaceShader')

    return [sgr,mat,lambert]

def assignShader(sgr,node):

    if cmds.sets([node],e=True,forceElement=sgr):
        print('[fxRenderLib.assignShader] - d' + sgr + ' correctly assigned to ' + node)    
        return 1
    else:
        return 0

def arnoldMotionVectorFromMesh(mesh,vscale=.1):
    '''
        Soup needs to be loaded, check to come
        This def create the network to do motion blur on imported abc in Maya/Arnold
        The imported alembic should have a Cd attribut ( or v ? )
    '''
    connection = cmds.connectionInfo(mesh+'.inMesh',sfd=True)
    print('[fxRenderLib.arnoldMotionVectorFromMesh] - connection = ' + connection)    
    if connection:
        connectionNode = connection.split('.')[0]
        print('[fxRenderLib.arnoldMotionVectorFromMesh] - connectionNode = ' + connectionNode)    
        colorSet = cmds.polyColorSet(mesh,create=True,colorSet='velocityPV')
        print('[fxRenderLib.arnoldMotionVectorFromMesh] - colorSet = ' + colorSet[0])
        try: 
            applyColor = cmds.polyColorPerVertex(mesh,a=1,cdo=True)
            #-r 0.5 -g 0.5 -b 0.5 -a 1 -cdo;
            print('[fxRenderLib.arnoldMotionVectorFromMesh] - applyColor = ' + str(applyColor))
        except:
            time = cmds.currentTime(q=True)
            print('[fxRenderLib.arnoldMotionVectorFromMesh] - cannont apply colorPerVertex as mesh has no vertex @frame ' + str(time))

        atpc = cmds.createNode('arrayToPointColor')
        print('[fxRenderLib.arnoldMotionVectorFromMesh] - atpc = ' + atpc)    
            
        cmds.connectAttr(connectionNode+'.prop[0]',atpc+'.inRgbaPP')
        
        connection = cmds.connectionInfo(mesh+'.inMesh',sfd=True)
        print('[fxRenderLib.arnoldMotionVectorFromAlembic] - connection = ' + connection)    
        connectionNode = connection.split('.')[0]
        print('[fxRenderLib.arnoldMotionVectorFromAlembic] - connectionNode = ' + connectionNode)    
        
        cmds.connectAttr(connection,atpc+'.inGeometry')
        cmds.disconnectAttr(connection,mesh+'.inMesh')
        cmds.connectAttr(atpc+'.outGeometry',mesh+'.inMesh',f=True)
        
        #cmds.setAttr(mesh+'.motionVectorColorSet','colorSet',type='string')
        cmds.setAttr(mesh+'.aiMotionVectorScale',vscale)
    else:
        print('[fxRenderLib.arnoldMotionVectorFromMesh] - No inMesh connection for ' + mesh + ' - this alembic is transformed only - can be motion blurred')    
    return 1

def arnoldMotionVectorFromAlembic(alembicNode,vscale=.1):
    '''
        Soup needs to be loaded, check to come
        This def create the network to do motion blur on imported abc in Maya/Arnold
        The imported alembic should have a Cd attribut ( or v ? )
    '''
    outPolyMeshAttr = cmds.listAttr(alembicNode+'.outPolyMesh',multi=True)
    for out in outPolyMeshAttr:
        connection = cmds.connectionInfo(alembicNode+'.'+out,dfs=True)
        print('[fxRenderLib.arnoldMotionVectorFromAlembic] - connection = ' + str(connection))
        connectionNode = connection.split('.')[0]
        print('[fxRenderLib.arnoldMotionVectorFromAlembic] - connectionNode = ' + connectionNode)    
        colorSet = cmds.polyColorSet(mesh,create=True,colorSet='velocityPV')
        print('[fxRenderLib.arnoldMotionVectorFromMesh] - colorSet = ' + colorSet[0])
        applyColor = cmds.polyColorPerVertex(mesh)
        print('[fxRenderLib.arnoldMotionVectorFromMesh] - applyColor = ' + str(applyColor))
        atpc = cmds.createNode('arrayToPointColor')
        print('[fxRenderLib.arnoldMotionVectorFromMesh] - atpc = ' + atpc)

def arnoldCreateMeshLight(mesh,aov=1):

    incidenceShape = cmds.createNode('mesh',n=mesh+'_incidenceShape')

    cmds.connectAttr(mesh+'.worldMesh[0]',incidenceShape+'.inMesh')
    cmds.setAttr(incidenceShape+'.aiTranslator','mesh_light',type='string')
    cmds.setAttr(incidenceShape+'.aiNormalize',0)
    cmds.setAttr(incidenceShape+'.aiSamples',10)
    cmds.setAttr(incidenceShape+'.aiAov',aov,type='string')
    print('[fxRenderLib.arnoldCreateMeshLight] - incidenceShape = ' + incidenceShape)

    incidenceParent = cmds.rename(cmds.listRelatives(incidenceShape,p=True)[0],mesh+'_incidence')
    print('[fxRenderLib.arnoldCreateMeshLight] - incidenceParent = ' + incidenceParent)

    return incidenceParent

