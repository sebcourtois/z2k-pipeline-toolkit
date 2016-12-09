import os, sys
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

print 'ok'

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

def generatePrivateCachePath(node=''):
   
    fullFileName = cmds.file(q=True,exn=True)
    print ('[generateCachePath.generatePrivateCachePath] - file full name = ' + fullFileName)
    fileName = cmds.file(q=True,exn=True).split('/')[-1].split('.ma')[0]
    print ('[generateCachePath.generatePrivateCachePath] - fileName = ' + fileName)
    fileVersion = fileName.split('-')[-1]
    print ('[generateCachePath.generatePrivateCachePath] - fileVersion = ' + fileVersion)
    localPath = ['/'.join(fullFileName.split('/')[:-1]),'fxCache',fileVersion]
    print ('[generateCachePath.generatePrivateCachePath] - localPath = ' + str(localPath))
    outPath = '/'.join(localPath)
    print ('[generateCachePath.generatePrivateCachePath] - outPath = ' + str(outPath))

    if node:
        print node
        nodeSplit=node
        if ':' in node:
            nodeSplit = node.split(':')[1]
            print nodeSplit
        nodeShape = cmds.listRelatives(node,s=True)[0]
        print nodeShape

        if nodeShape and (cmds.nodeType(nodeShape) == 'nParticle' or cmds.nodeType(nodeShape) == 'fluidShape' or cmds.nodeType(nodeShape) == 'BE_VDBArnoldRender'):
            nodeSplit='pkg_'+nodeSplit

        outPath = '/'.join([outPath,nodeSplit])


    if not os.path.isdir(outPath):
        #print 'is not dir'
        os.makedirs(outPath)
        #print 'created'

    normPath = os.path.normpath(outPath)

    if node:
        pm.warning('[generateCachePath.generatePrivateCachePath] - outPath for ' + node + ' = ' + outPath)
        pm.warning('[generateCachePath.generatePrivateCachePath] - normPath for ' + node + ' = ' + normPath)
    else:
        pm.warning('[generateCachePath.generatePrivateCachePath] - outPath for current scene = ' + outPath)
        pm.warning('[generateCachePath.generatePrivateCachePath] - normPath for current scene = ' + normPath)

    return outPath, normPath