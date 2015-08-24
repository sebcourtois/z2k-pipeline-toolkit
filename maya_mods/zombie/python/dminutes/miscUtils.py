import maya.cmds as mc
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
        raise ValueError("#### error 'getMeshesWithSameName': No '"+str(inParent)+"' found")
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