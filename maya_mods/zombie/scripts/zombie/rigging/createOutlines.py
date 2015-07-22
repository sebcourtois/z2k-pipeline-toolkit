import pymel.core as pc

def getShaders(inObj, inFirstOnly=False):
    shaders = []
    shapes = [inObj]
    if inObj.type() == "transform":
        shapes = inObj.getShapes(noIntermediate=True)

    for shape in shapes:
        shadingGroups = pc.listConnections(shape, type="shadingEngine", connections=True, source=False, plugs=True)
        for sGroupConnection in shadingGroups:
            print sGroupConnection
            comps=None
            if "objectGroups" in sGroupConnection[0].name():
                comps = pc.getAttr(sGroupConnection[0].name() + '.objectGrpCompList')
            sGroup = sGroupConnection[1].node()
            
            cons = pc.listConnections(sGroup, destination=False)
            for con in cons:
                if con.type() != "transform":
                    shadingInfo = (con, comps if comps != None else shape)
                    shaders.append(shadingInfo)
                    if inFirstOnly:
                        return shaders
                    break

    return shaders

def getShadingGroup(inMaterial):
    nodes = pc.listHistory(inMaterial, future=True, levels=1)
    shadingGroup = None
    
    for node in nodes:
        if node.type() == "shadingEngine" or node.type() == "materialFacade":
            shadingGroup = node
            break

    #No shading group ?
    if shadingGroup == None:
        shadingGroup = pc.sets(renderable=True, noSurfaceShader=True, empty=True, name=inMaterial.name()+"SG")
        pc.connectAttr(inMaterial.name() + ".outColor", shadingGroup.name() + ".surfaceShader")

    return shadingGroup

def assignShader(inMaterial, inObj, inSG=None):
    #print "assignShader(%s, %s, %s, %s)" % (str(inMaterial), str(inObj), str(inSG), str(inMultiUVs))

    shape = inObj
    if inObj.type() == "transform":
        shape = inObj.getShape()

    shadingGroup = None

    if inSG != None:
        shadingGroup = inSG
    else:
        shadingGroup = getShadingGroup(inMaterial)

    pc.sets(shadingGroup, edit=True, forceElement=shape)

    return shadingGroup

def cleanShapes():
    junk = []
    meshes = pc.ls(type="mesh")
    for mesh in meshes:
        if not pc.ls(pc.listHistory(mesh, allFuture=True), type='shape', ni=True):
            print "{0} is not necessary".format(mesh)
            pc.delete(mesh)

def createOutlines():
    meshes = pc.ls("*:geo_*", type="mesh")
    oldMeshes = list(meshes)
    meshes = []
    
    for oldMesh in oldMeshes:
        transform = oldMesh.getParent()
        if not transform in meshes:
            meshes.append(transform)
    
    #Get the namespace of the first found mesh
    ns = ""
    
    if ':' in meshes[0].name():
        #I can't find a maya command to get the namespace of a node, so let's use a string split with ':' character
        ns = meshes[0].name().split(':')[0] + ':'
    
    dupes = pc.duplicate(meshes, returnRootsOnly=True, inputConnections=False)
    moveVertexNodes = {}
    
    cnt = 0
    for dupe in dupes:
        origObj = meshes[cnt]
    
        shape = dupe.getShape()
        pc.setAttr(shape.name() + ".doubleSided", 0)
        pc.setAttr(shape.name() + ".opposite", 1)
        moveVertNode = pc.polyMoveVertex(dupe, localTranslateZ=0.01)[0]
        pc.rename(dupe, ns + "outline_" + dupe.name())
        
        moveVertexNodes[dupe.name()] = moveVertNode
        
        #remove copied constraint
        oldCons = pc.ls(pc.listRelatives(dupe, children=True), type="constraint")
        if len(oldCons) > 0:
            pc.delete(oldCons)
        
        #get original constraint target
        cns = pc.listConnections(origObj, type="constraint", destination=False)
        if len(cns) > 0:
            target = pc.listConnections(cns[0].name() + '.target', destination=False)
            pc.parentConstraint( target, dupe, mo=True )
    
        cnt += 1
    
    #clean des materiaux inutilises et cree un mat noir
    pc.mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')
    blackLineShader = None
    blackLines = pc.ls("black_line", type="surfaceShader")
    
    if len(blackLines) == 0:
        blackLineShader = pc.shadingNode("surfaceShader", name='black_line', asShader=True)
        pc.setAttr(blackLineShader.name() + '.outColor', [0,0,0], type='double3')
    else:
        blackLineShader = blackLines[0]
    
    #applique le mat sur les nouveaux objets
    
    cnt = 0
    SG = None
    for dupe in dupes:
        origObj = meshes[cnt]
    
        SG = assignShader(blackLineShader, dupe, SG)
        #applique le mat sur les nouveaux objets
        #re-plug the input mesh to ref mesh (to keep blendshapes)
        moveVertNode = moveVertexNodes[dupe.name()]
        oldShape = pc.listConnections(moveVertNode.name() + ".inputPolymesh", destination=False, shapes=True)[0]
    
        pc.disconnectAttr(oldShape.name() + '.outMesh', moveVertNode.name() + '.inputPolymesh')
        pc.delete(oldShape)
        
        pc.connectAttr(origObj.getShape().name() + ".outMesh", moveVertNode.name() + ".inputPolymesh")
        
        #connecting smooth
        #connectAttr -force aurelien_tShirtRock_previz_MASTER:geo_Left_Eye_Main_CtrlShape.smoothLevel aurelien_tShirtRock_previz_MASTER:outline_geo_Head_Ctrl_Bone_CtrlShape.smoothLevel;
        cnt += 1
    
    #put all outline under a group
    pc.group(dupes, name=ns + "grp_outlines")

createOutlines()