import os, sys
import maya.cmds as cmds
import maya.mel as mel

paths = ['//zombiwalk/ZOMBIWALK/Z2K/06_PARTAGE/sebastienr/TOOLS/libs']

for path in paths:
    if path not in sys.path:
        sys.path.insert(0,path)

import fxMeshLib as fxm
reload(fxm)

def generateCachePath(node):
    from davos_maya.tool.general import infosFromScene
    from dminutes import maya_scene_operations as mop
    scnInfos = infosFromScene()
    print scnInfos
    path = mop.getMayaCacheDir(scnInfos["dam_entity"])
    print path
    fileName = cmds.file(q=True,sn=True).split('/')[-1].split('.ma')[0].split('.')
    print fileName
    message = ('/'.join((path,scnInfos["step"],fileName[0],fileName[1],node))).replace('alembic','')
    print message
    if os.path.isdir(message):
    	print 'is dir'
    else:
    	print 'is not dir'
    	#os.makedirs(message)
    	print 'created'
    mel.eval('warning("'+message+'")')
    return message

def generatePrivateCachePath():
   
    fullFileName = cmds.file(q=True,exn=True)
    print ('[generateCachePath.generatePrivateCachePath] - file full name = ' + fullFileName)
    fileName = cmds.file(q=True,exn=True).split('/')[-1].split('.ma')[0]
    print ('[generateCachePath.generatePrivateCachePath] - fileName = ' + fileName)
    fileVersion = fileName.split('-')[-1]
    print ('[generateCachePath.generatePrivateCachePath] - fileVersion = ' + fileVersion)
    localPath = ['/'.join(fullFileName.split('/')[:-1]),'fxCache',fileVersion]
    print ('[generateCachePath.generatePrivateCachePath] - localPath = ' + str(localPath))
    outPath = '/'.join(localPath)
    print ('[generateCachePath.generatePrivateCachePath] - outPath = ' + outPath)

    if not os.path.isdir(outPath):
        #print 'is not dir'
        os.makedirs(outPath)
        #print 'created'
    return outPath