#=========================================================================================
#
#                    SOuP Library by sebR
#
#=========================================================================================

#TODO : rajouter un test si plugin loaded ou pas

#-----------------------------------------------------------------------------------------
import maya.cmds as cmds
import maya.mel as mel
#import fxMayaGeoLib as fxmg
#-----------------------------------------------------------------------------------------

def soupIsLoaded():
    if cmds.pluginInfo('SOuP',q=True,l=True):
        return 1
    else:
        warningMessage='warning(\"SOuP plugin is not loaded - please load it\")\n'
        mel.eval(warningMessage)
        return 0

def buildTransformNetwork(meshTransform):
    '''
        Get a Mesh, if it's parented or not ( BOOL ), create network for Global transform driven by meshTransform
    '''   
    if soupIsLoaded():

        shape = cmds.listRelatives(meshTransform,s=True)
    
        if cmds.nodeType(shape[0]) == 'mesh':
            parent = cmds.listRelatives(meshTransform,p=True)
            shape = cmds.listRelatives(meshTransform,s=True)
            
            transformGeometry = cmds.createNode('transformGeometry',n=meshTransform+'_transformGeometry')
            transformGeometry = cmds.rename(meshTransform + '_transformGeometry')
            transformNode = cmds.createNode('transform',n=meshTransform+'_transform')
            transformNode = cmds.rename(meshTransform + '_transform')
            
            connections = cmds.connectionInfo(shape[0]+'.outMesh',dfs=True)
            
            cmds.connectAttr(shape[0]+'.outMesh',transformGeometry+'.inputGeometry',f=True)
            if connections:
                for connec in connections:
                    cmds.connectAttr(transformGeometry+'.outputGeometry',connec,f=True)
            cmds.connectAttr(transformNode+'.worldMatrix[0]',transformGeometry+'.transform',f=True)
            
            if not parent:
                cmds.connectAttr(meshTransform+'.translate',transformNode+'.translate')
                cmds.connectAttr(meshTransform+'.rotate',transformNode+'.rotate')
                cmds.connectAttr(meshTransform+'.scale',transformNode+'.scale')
            else:
                cmds.parent(transformNode,parent)
            
            print ('[buildTransformNetwork] - Transform network succesfully created for ' + meshTransform)
            return [transformGeometry,transformNode]
        else:
            print (meshTransform + ' is not a mesh - skipped')
            return 0


def introduceBoundingObject(meshTransform,soupNode):
    
    '''
        get a soupNode, a meshShape and connect it as a boundingObject
    '''
    if soupIsLoaded():
        command = 'python("soup().create(\'boundingObject\')")'
        boundingObject=mel.eval(command)
        if meshTransform:
            shape = cmds.listRelatives(meshTransform,s=True)
            if cmds.nodeType(meshTransform) == 'transformGeometry':
                cmds.connectAttr(meshTransform+'.outputGeometry', boundingObject[1]+'.inMesh')
            elif cmds.nodeType(shape[0]) == 'mesh':
                cmds.connectAttr(shape[0]+'.outMesh', boundingObject[1]+'.inMesh')
            cmds.expression(boundingObject[1],s=boundingObject[1]+'.type = 3;',ae=True,uc='all')
            cmds.setAttr(boundingObject[1]+'.displayPointCloudBoundingVolumes',0)
        
        numberOfConnections = cmds.listConnections( soupNode + '.boundingObjects', d=False, s=True )
        if not numberOfConnections:
            numberOfConnections = 0
        else:
            numberOfConnections = len(numberOfConnections)/2+1
            
        cmds.connectAttr(boundingObject[1]+'.outData',soupNode+'.boundingObjects['+ str(numberOfConnections) +']')
        cmds.connectAttr(boundingObject[1]+'.outParentMatrix',soupNode+'.boundingObjects['+ str(numberOfConnections) +'].boundParentMatrix')
        
        return boundingObject

def addLocalSmooth(meshTransform,BoundingObjectMesh=''):
    
    if soupIsLoaded():
        group = cmds.createNode('group')
        cmds.setAttr(group+'.componentType',2)
        polySmooth = cmds.createNode('polySmoothFace')
        outShapes = fxmg.addShapeOrig(meshTransform)
        
        cmds.connectAttr(outShapes[1]+'.outMesh',group+'.inGeometry')
        cmds.connectAttr(group+'.outComponents',polySmooth+'.inputComponents')
        cmds.connectAttr(group+'.outGeometry',polySmooth+'.inputPolymesh')
        cmds.connectAttr(polySmooth+'.output',outShapes[0]+'.inMesh',f=True)    
        
        boundingObject = introduceBoundingObject(BoundingObjectMesh,group)
        
        outBounding = cmds.rename(boundingObject[0],meshTransform+'_boundingObject')
        
        return [outShapes[0],outShapes[1],outBounding]

def autoWrap(keepHistory=False):
    #Write output, return value
    if soupIsLoaded():
        selection = cmds.ls(sl=True,l=True)
        outGroup=[]
        
        if not selection:
            message = 'warning("[AUTO WRAP] - You must select at least 1 mesh")'
            mel.eval(message)
        else:
            for item in selection:
                itemShort = cmds.ls(item,sn=True)
                shape = cmds.listRelatives(item,s=True,f=True)
                if cmds.nodeType(shape[0]) == 'mesh':

                    cmds.xform(item,cp=True)
                    dupli = cmds.duplicate(item,rr=True,rc=True)

                    dupli = dupli[0]
                    try:
                        cmds.parent(dupli,w=True,a=True)
                    except:
                        print '[AUTO WRAP] - ' + dupli + ' is already parented to world - skipped'
                    cmds.makeIdentity(dupli,apply=True,t=1,r=1,s=1,n=0)
                    
                    boundingBox = fxmg.getBoundingBox(dupli)
                    dif = max([boundingBox[1] - boundingBox[0], boundingBox[3] - boundingBox[2], boundingBox[5] - boundingBox[4]])
                    
                    sphere = cmds.polySphere()
                    
                    constraint = cmds.pointConstraint(item,sphere[0],mo=False,weight=1)
   
                    polySphere = cmds.connectionInfo(sphere[0]+'.inMesh',sfd=True).split('.')[0]
                    cmds.delete(constraint[0])
                    
                    command = 'python("soup().create(\'attributeTransfer\')")'
                    attributeTransfer=mel.eval(command)
                    attributeTransfer=cmds.createNode('attributeTransfer')
                    cmds.setAttr(attributeTransfer+'.position',1)
                    cmds.setAttr(attributeTransfer+'.maxInfluences',1)
                    
                    boundingObject = introduceBoundingObject(dupli,attributeTransfer)
                    cmds.removeMultiInstance(boundingObject[1]+'.positionFalloff[1]',b=True)
                    
                    cmds.connectAttr(sphere[0]+'.worldMesh[0]',attributeTransfer+'.inGeometry')
                    
                    cube = cmds.polyCube()
                    cubeShape = cmds.listRelatives(cube[0],s=True)[0]
                    cmds.connectAttr(attributeTransfer+'.outGeometry',cubeShape+'.inMesh',f=True)
                    cmds.delete(cube[1])
                    
                    connection = cmds.connectionInfo(dupli+'.shear',sfd=True)
                    if connection:
                        cmds.delete(connection.split('.')[0])
                        
                    cmds.xform(cube[0],cp=True)
                    cmds.polyMergeVertex(cube[0],d=0.01,am=True,ch=True)
                    cmds.polySoftEdge(cube[0],a=False,ch=True)
                    
                    group =''
                    if keepHistory:
                        print 'keepHistory'
                        group = cmds.group(em=True,n=itemShort[0]+'_WRAPGROUP')
                        cmds.addAttr(group,ln='WRAP_CTRL',at='enum',en=' ')
                        cmds.setAttr(group+'.WRAP_CTRL',e=True,k=True,l=True)
                        cmds.addAttr(group,ln='wrapRadius',at='double',min=1,dv=500,k=True)
                        cmds.addAttr(group,ln='wrapBoundRadius',at='double',min=1,dv=500,k=True)
                        cmds.addAttr(group,ln='wrapRezX',at='double',min=1,dv=10,k=True)
                        cmds.addAttr(group,ln='wrapRezY',at='double',min=1,dv=10,k=True)
                        cmds.addAttr(group,ln='displayWrapped',at='bool',dv=0,k=True)
                        cmds.addAttr(group,ln='displayWrapper',at='bool',dv=0,k=True)
                        cmds.setAttr(group+'.wrapBoundRadius',dif*2)
                        cmds.setAttr(group+'.wrapRadius',dif)
                        
                        cmds.parent(dupli,group)
                        cmds.parent(sphere[0],group)
                        cmds.parent(cube[0],group)
                        cmds.parent(boundingObject[0],group)
                        
                        cmds.setAttr(sphere[0]+'.visibility',0)
                        cmds.displaySurface(sphere[0],xRay=1)
                        cmds.setAttr(dupli+'.visibility',0)
                        
                        cmds.connectAttr(group+'.wrapRadius',sphere[0]+'.sx')
                        cmds.connectAttr(group+'.wrapRadius',sphere[0]+'.sy')
                        cmds.connectAttr(group+'.wrapRadius',sphere[0]+'.sz')
                        cmds.connectAttr(group+'.wrapBoundRadius',boundingObject[1]+'.pointRadius')
                        cmds.connectAttr(group+'.wrapRezX',polySphere+'.subdivisionsAxis')
                        cmds.connectAttr(group+'.wrapRezY',polySphere+'.subdivisionsHeight')
                        cmds.connectAttr(group+'.displayWrapped',sphere[0]+'.visibility')
                        cmds.connectAttr(group+'.displayWrapper',dupli+'.visibility')
                        outGroup.append(group)
                        cmds.select(group)
                        
                    else: 
                        group = cmds.group(em=True,n='WRAPGROUP')
                        cmds.parent(cube[0],group)
                        cmds.setAttr(boundingObject[1]+'.pointRadius',dif*2)
                        cmds.setAttr(sphere[0]+'.sx',dif)
                        cmds.setAttr(sphere[0]+'.sy',dif)
                        cmds.setAttr(sphere[0]+'.sz',dif)
                        
                        cmds.delete(cube[0],ch=True)
                        cmds.delete(dupli)
                        cmds.delete(sphere)
                        outGroup.append(group)          
                        
                    print('[AUTO WRAP] - ' + item + ' succesfully wrapped')
            
            return outGroup
                    
                    
        
def autoProject(keepHistory=False):
        #Write output, return value
        
        if soupIsLoaded():
            selection = cmds.ls(sl=True,l=True)
        
        outGroup=[]
        if not selection:
            message = 'warning("[AUTO PROJECT] - You must select at least 1 mesh")'
            mel.eval(message)
        else:

            for item in selection:
                itemShort = cmds.ls(item,sn=True)
                shape = cmds.listRelatives(item,s=True,f=True)
                if cmds.nodeType(shape[0]) == 'mesh':

                    cmds.xform(item,cp=True)
                    dupli = cmds.duplicate(item,rr=True,rc=True)

                    dupli = dupli[0]
                    try:
                        cmds.parent(dupli,w=True,a=True)
                    except:
                        print '[AUTO PROJECT] - ' + dupli + ' is already parented to world - skipped'
                    
                    cmds.makeIdentity(dupli,apply=True,t=1,r=1,s=1,n=0)
                    
                    boundingBox = fxmg.getBoundingBox(dupli)
                    dif = max([boundingBox[1] - boundingBox[0], boundingBox[3] - boundingBox[2], boundingBox[5] - boundingBox[4]])
                
                    plane = cmds.polyPlane()
                    constraint = cmds.pointConstraint(item,plane[0],mo=False,weight=1)
   
                    polyPlane = cmds.connectionInfo(plane[0]+'.inMesh',sfd=True).split('.')[0]
                    cmds.delete(constraint[0])
                    
                    command = 'python("soup().create(\'rayProject\')")'
                    rayProject=mel.eval(command)
                    
                    cmds.connectAttr(cmds.listRelatives(item,s=True)[0]+'.worldMesh[0]',rayProject+'.inCollisionMesh')
                    cmds.connectAttr(cmds.listRelatives(plane[0],s=True)[0]+'.worldMesh[0]',rayProject+'.inGeometry')
                    
                    cube = cmds.polyCube()
                    cubeShape = cmds.listRelatives(cube[0],s=True)[0]
                    cmds.connectAttr(rayProject+'.outGeometry',cubeShape+'.inMesh',f=True)
                    cmds.delete(cube[1])
                    
                    connection = cmds.connectionInfo(dupli+'.shear',sfd=True)
                    if connection:
                        cmds.delete(connection.split('.')[0])
                        
                    cmds.xform(cube[0],cp=True)
                
                
                    if keepHistory:
                        group = cmds.group(em=True,n=itemShort[0]+'_PROJECTGROUP')
                        cmds.addAttr(group,ln='PROJECT_CTRL',at='enum',en=' ')
                        cmds.setAttr(group+'.PROJECT_CTRL',e=True,k=True,l=True)
                        cmds.addAttr(group,ln='projectTY',at='double',dv=500,k=True)
                        cmds.addAttr(group,ln='projectSize',at='double',min=1,dv=0,k=True)
                        cmds.addAttr(group,ln='projectRezX',at='double',min=1,dv=10,k=True)
                        cmds.addAttr(group,ln='projectRezY',at='double',min=1,dv=10,k=True)
                        cmds.addAttr(group,ln='displayProjected',at='bool',dv=0,k=True)
                        cmds.addAttr(group,ln='displayCollider',at='bool',dv=0,k=True)
                        
                        cmds.parent(dupli,group)
                        cmds.parent(plane[0],group)
                        cmds.parent(cube[0],group)
                        
                        cmds.setAttr(plane[0]+'.visibility',0)
                        cmds.displaySurface(plane[0],xRay=1)
                        cmds.setAttr(dupli+'.visibility',0)
                                              
                        cmds.connectAttr(group+'.projectTY',plane[0]+'.ty')
                        cmds.connectAttr(group+'.projectSize',plane[0]+'.sz')
                        cmds.connectAttr(group+'.projectSize',plane[0]+'.sx')
                        cmds.connectAttr(group+'.projectRezX',polyPlane+'.subdivisionsWidth')
                        cmds.connectAttr(group+'.projectRezY',polyPlane+'.subdivisionsHeight')
                        cmds.connectAttr(group+'.displayProjected',plane[0]+'.visibility')
                        cmds.connectAttr(group+'.displayCollider',dupli+'.visibility')
                        
                        cmds.setAttr(group+'.projectSize',dif)
                        cmds.setAttr(group+'.projectTY',0)
                        outGroup.append(group)
                        cmds.select(group)
                    else:
                        group = cmds.group(em=True,n='PROJECTGROUP')
                        cmds.parent(cube[0],group)
                        cmds.setAttr(plane[0]+'.sx',dif)
                        cmds.setAttr(plane[0]+'.sy',dif)
                        cmds.setAttr(plane[0]+'.sz',dif)
                        outGroup.append(group)
 
                    cmds.rename(cube[0],item+'_Projected#')
                    print('[AUTO PROJECT] - ' + item + ' succesfully projected')
            return outGroup

def motionBlurAlembicArnold(alembicMesh):

    if soupIsLoaded():
        shape = cmds.listRelatives(alembicMesh,s=True)[0]
        print shape
        alembicNode = cmds.listConnections(shape+'.inMesh')[0]
        print alembicNode
        array = cmds.createNode('arrayToPointColor')
        print array
        colorSetName = cmds.polyColorSet(alembicMesh,create=True,clamped=False,rpt='RGBA',colorSet="colorSet")[0]
        print colorSetName
        colorSetNode = cmds.listConnections(shape+'.inMesh')[0]
        print colorSetNode
        cmds.connectAttr(alembicNode+'.outPolyMesh[0]',array+'.inGeometry')
        cmds.connectAttr(alembicNode+'.prop[0]',array+'.inRgbaPP')
        
        try:
            cmds.connectAttr(array+'.outGeometry',colorSetNode+'.inputGeometry',f=True)
        except:
            cmds.disConnectAttr(alembicNode+'.outPolyMesh[0]',colorSetNode+'.inputGeometry')
            cmds.connectAttr(array+'.outGeometry',colorSetNode+'.inputGeometry',f=True)

        cmds.setAttr(shape+'.aiMotionVectorSource',colorSetName,type='string')
        cmds.setAttr(shape+'.aiMotionVectorScale',0)

        return 1
    else:
        return 0