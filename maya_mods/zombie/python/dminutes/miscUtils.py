import maya.cmds as mc
import pymel.core as pm
import os


def getAllTransfomMeshes(inParent = "*"):
    """
    list all the transforms meshes , under de given 'inParent', 
    by default '*' means that any unreferenced transform mesh in the scene will be listed
        - inParent (string) : long name of the parent 
        - return (list) : allTransMesh
    """ 
    oParent = mc.ls(inParent, l =True)
    if not oParent:
        raise ValueError("#### error 'getAllTransfomMeshes': No '"+str(inParent)+"' found")
    elif inParent != "*":
        oParent = oParent[0]
    else:
        oParent = "*"
        
    geoShapeList = mc.ls(mc.listRelatives(oParent, allDescendents = True, fullPath = True, type = "mesh"), noIntermediate = True, l=True)
    allTransMesh = mc.listRelatives (geoShapeList, parent = True, fullPath = True, type = "transform")
    if allTransMesh is None: allTransMesh = []

    return allTransMesh


def pathJoin(*args):
    return normPath(os.path.join(*args))

def normPath(p):
    return os.path.normpath(p).replace("\\",'/')



def createUserWorkspace():
    try:
        davosUser = os.environ["DAVOS_USER"]
    except:
        raise ValueError("#### Error: DAVOS_USER environement variable is not defined, please log to davos")

    if davosUser not in mc.workspace(listWorkspaces = True):

        workspaceDir = os.path.split(normPath(mc.workspace( 'default',q=True, dir=True )))[0]
        projectPath = (normPath(os.path.join(workspaceDir, davosUser)))
        if not os.path.isdir(projectPath):
            print "#### Info: create project: "+projectPath
            mc.workspace( davosUser, newWorkspace=True)

            os.mkdir(projectPath)
            os.makedirs(normPath(os.path.join(projectPath,"cache","nCache","fluid")))
            os.makedirs(normPath(os.path.join(projectPath,"data")))
            os.makedirs(normPath(os.path.join(projectPath,"images")))
            os.makedirs(normPath(os.path.join(projectPath,"sourceimages","3dPaintTextures")))
            os.makedirs(normPath(os.path.join(projectPath,"scripts")))
            os.makedirs(normPath(os.path.join(projectPath,"movies")))
            os.makedirs(normPath(os.path.join(projectPath,"scenes")))
            os.makedirs(normPath(os.path.join(projectPath,"scenes","edits")))
            os.makedirs(normPath(os.path.join(projectPath,"autosave")))
            os.makedirs(normPath(os.path.join(projectPath,"sound")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData")))
            os.makedirs(normPath(os.path.join(projectPath,"clips")))
            os.makedirs(normPath(os.path.join(projectPath,"assets")))
            os.makedirs(normPath(os.path.join(projectPath,"cache","bifrost")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furShadowMap")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","shaders")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furFiles")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furEqualMap")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furImages")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","iprImages")))
            os.makedirs(normPath(os.path.join(projectPath,"cache","particles")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","depth")))
            os.makedirs(normPath(os.path.join(projectPath,"renderData","fur","furAttrMap")))    
            pm.mel.setProject(projectPath)
    
    print "#### Info: set project: "+ davosUser
    pm.workspace( davosUser, openWorkspace = True )

        
def deleteUnknownNodes():
    
    mentalRayNodeList = [u'mentalrayGlobals',u'mentalrayItemsList',u'miDefaultFramebuffer',u'miDefaultOptions',u'Draft',u'DraftMotionBlur',u'DraftRapidMotion',u'Preview',
                            u'PreviewCaustics',u'PreviewFinalGather',u'PreviewGlobalIllum',u'PreviewImrRayTracyOff',u'PreviewImrRayTracyOn',u'PreviewMotionblur',
                            u'PreviewRapidMotion',u'Production',u'ProductionFineTrace',u'ProductionMotionblur',u'ProductionRapidFur',u'ProductionRapidHair',
                            u'ProductionRapidMotion',u'miContourPreset']
    turtleNodeList = [u'TurtleDefaultBakeLayer',u'TurtleBakeLayerManager',u'TurtleRenderOptions',u'TurtleUIOptions']

    mentalRayNodeList = mc.ls(mentalRayNodeList)
    turtleNodeList= mc.ls(turtleNodeList)
    mentalRayDeletedNodeList = []
    turtleDeletedNodeList = []

    for each in mentalRayNodeList:
        try:
            mc.lockNode(each,lock = False)
            mc.delete(each)
            mentalRayDeletedNodeList.append(each)
            #print "#### {:>7}: '{}' Mental Ray node deleted".format("Info", each)
        except:
            print "#### {:>7}: '{}' Mental Ray node could not be deleted".format("Warning", each)

    for each in turtleNodeList:
        try:
            mc.lockNode(each,lock = False)
            mc.delete(each)
            turtleDeletedNodeList.append(each)
            #print "#### {:>7}: '{}' Turtle node deleted".format("Info", each)
        except:
            print "#### {:>7}: '{}' Turtle node could not be deleted".format("Warning", each)

    unknownNodes = mc.ls(type = "unknown")
    if unknownNodes:
        print "#### {:>7}: '{}' unknown node has been found in the scene".format("Warning", len(unknownNodes))
        print "#### {:>7}: unknown node list:'{}'".format("Warning", unknownNodes)

    if mentalRayDeletedNodeList:
        print "#### {:>7}: '{}' Mental Ray node(s) deteled: '{}'".format("Warning", len(mentalRayDeletedNodeList), mentalRayDeletedNodeList)

    if turtleDeletedNodeList:
        print "#### {:>7}: '{}' Turtle node(s) deteled: '{}".format("Warning", len(turtleDeletedNodeList), turtleDeletedNodeList)


    try:
        mc.unloadPlugin("Turtle",force = True)
    except:
        pass



def setAttrC(*args, **kwargs):
    try:
        mc.setAttr(*args, **kwargs)
        return True
    except:
        print "#### {:>7}: setAttr {}{} not possible, attribute is locked or connected".format("Warning", args, kwargs)
        return False


def removeAllNamespace ( NSexclusionL = [""], limit = 100, verbose = False, emptyOnly=False, *args,**kwargs):
        """ Description: Delete all NameSpace appart the ones in the NSexclusionL
            Return : nothing
            Dependencies : cmds - 
        """
        tab= "    "
        #print "removeAllNamespace()"
        toReturnB = True
        # "UI","shared" NS are used by maya itself
        NS_exclusionBL=["UI","shared"]
        NS_exclusionBL.extend(NSexclusionL)
        # set the current nameSpace to the root nameSpace
        mc.namespace(setNamespace = ":")
        # get NS list
        nsL = mc.namespaceInfo(listOnlyNamespaces=True)# list content of a namespace  
        

        for loop in range(len(nsL)+2):
            nsL = mc.namespaceInfo(listOnlyNamespaces=True)
            for ns in nsL:
                if ns not in NS_exclusionBL:
                    if emptyOnly == False:
                        if verbose: print tab+"ns:",ns
                        mc.namespace( removeNamespace =ns, mergeNamespaceWithRoot=True)
                    else:
                        if not mc.namespaceInfo(ns,  listOnlyDependencyNodes= True):
                            if verbose: print tab+"ns:",ns
                            mc.namespace( removeNamespace =ns, mergeNamespaceWithRoot=True)

        # recursive
        if emptyOnly==False:
            count = 0
            nsLFin = mc.namespaceInfo(listOnlyNamespaces=True)
            while len(nsLFin)>2:
                removeAllNamespace(NSexclusionL = NSexclusionL, emptyOnly = emptyOnly, verbose= verbose)
                count += 1
                if count > limit:
                    break

        return [toReturnB]




def getShape(objectList =  [], failIfNoShape = False):
        shapeList = []
        for eachObject in objectList:
            if not mc.objectType(eachObject,isAType = "shape"):
                eachObjectShapes = mc.ls(mc.listRelatives(eachObject, noIntermediate = True, shapes = True, fullPath = True),l=False)
                if not eachObjectShapes and failIfNoShape:
                    raise ValueError("'{}' has no shape".format(eachObject))
                if len(eachObjectShapes)>1: 
                    raise ValueError("'{}' has several shapes".format(eachObject))
                shapeList.append(eachObjectShapes[0])
            else:
                shapeList.append(eachObject)
        return shapeList if shapeList != [] else  None


            
def deleteAllColorSet(inParent = "*"):
    sTransList = getAllTransfomMeshes(inParent = inParent)
    sMeshList = mc.ls(sTransList, type='mesh')
    nbOfDeleteDone=0
    for each in sTransList:
        if mc.polyColorSet(each, query=True, allColorSets=True):       
            mc.polyColorSet(each, delete=True)
            nbOfDeleteDone +=1
    print "#### {:>7}: color sets have been deleted on  {} objects".format("Info",nbOfDeleteDone )