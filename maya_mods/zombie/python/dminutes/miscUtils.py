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

        
        