
# jipe Z2K lib Wrappers


from davos.core import damproject
reload(damproject)
from davos.core.damtypes import DamAsset

import os, sys
import maya.cmds as cmds
import maya.mel as mel


def projConnect(theProject="zombtest",*args,**kwargs):
    """
    Description: Connect to Z2K DamProject
    Args : theProject = "zombtest"/"zomb"
    """
    print "Z2K_Connect()"
    tab= "    "
    

    DamProject = damproject.DamProject
    # proj = DamProject("zombtest")
    proj = DamProject(os.environ["DAVOS_INIT_PROJECT"])
    print tab,"proj=", proj
    return proj

def getPath(proj="", assetName="", pathType="previz_ref", *args, **kwargs):
    print "Z2K_getPath()"
    tab= "    "
    damAst =DamAsset(proj,name=assetName)
    path_public = damAst.getPath("public", pathType)
    path_private = damAst.getPath("private", pathType)
    print tab,"path_public=", path_public
    print tab,"path_private=", path_private

    return path_public,path_private

def openFileReadOnly(proj="",Path_publish_public="", *args, **kwargs):
    print "openFileReadOnly()"
    tab= "    "
    if not os.path.exists(Path_publish_public):
        with open(Path_publish_public, 'w') as f:
            f.write('')
        
    pubFile = proj.entryFromPath(Path_publish_public)
    # privFile = pubFile.__class__.__base__.edit(pubFile)
    privFile = pubFile.mayaOpen()

    print tab,"public_file_Version=",pubFile.currentVersion
    print tab, "privFile=",privFile

    return privFile

def editFile(proj="" ,Path_publish_public="", *args, **kwargs):
    print "Z2K_editFile()"
    tab= "    "
    if not os.path.exists(Path_publish_public):
        with open(Path_publish_public, 'w') as f:
            f.write('')
        
    pubFile = proj.entryFromPath(Path_publish_public)
    # privFile = pubFile.__class__.__base__.edit(pubFile)
    privFile = pubFile.edit(openFile=False)

    print tab,"public_file_Version=",pubFile.currentVersion
    print tab,"private_file_Version=",privFile.currentVersion

    return privFile

def publishFile(proj="", path_private_toPublish="",comment="test the cashbah moda foka!",*args, **kwargs):
    print "Z2K_publishFile()" 
    tab= "    "
    sPrivPath = path_private_toPublish.absPath()
    shortPublishedFileName= proj.publishEditedVersion(sPrivPath, comment="RockTheCashbah", autoLock=True)[0]
    PublishedFile_absPath = shortPublishedFileName.absPath()
    PublishedFile_shortName = shortPublishedFileName.fileName() 
    # PublishedFile_Comment = shortPublishedFileName.comment()
    
    print tab,"DONE","->",PublishedFile_shortName

    return PublishedFile_absPath