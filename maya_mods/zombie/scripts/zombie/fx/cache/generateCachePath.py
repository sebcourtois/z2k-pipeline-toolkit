import os
import maya.cmds as cmds
import maya.mel as mel

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

def generatePrivateCachePath(node):

	fullFileName = cmds.file(q=True,exn=True)
	fileName = cmds.file(q=True,exn=True).split('/')[-1].split('.ma')[0]
	fileVersion = fileName.split('-')[-1]
	localPath = ['/'.join(fullFileName.split('/')[:-1]),'fxCache',fileVersion,'pkg_'+node]
	message = '/'.join(localPath)
	if not os.path.isdir(message):
		#print 'is not dir'
		os.makedirs(message)
		#print 'created'
	mel.eval('warning("'+message+'")')
	return message
