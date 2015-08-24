import pymel.core as pc
import os

from davos.core import damproject

from davos_maya.core import mrclibrary
MrcLibrary = mrclibrary.MrcLibrary

import dminutes.maya_scene_operations as mop

PROJECTNAME = "zombillenium"

noneValue = 'None !'
notFoundvalue = 'Not found !'

#FROM DAVOS !!!!
ASSET_TYPES = ('Character 3D', 'Character 2D', 'Vehicle 3D', 'Prop 3D', 'Set 3D', 'Set 2D', 'Environment', 'Reference')
ASSET_SUBTYPES = ('1-primaire', '2-secondaire', '3-tertiaire', '4-figurant')
TASK_FILE_REL = {'previz 3D':'previz_scene'}
LIBS = {'Asset':'asset_lib', 'Shot':'shot_lib'}
FILE_SUFFIXES = {'Previz 3D':'_previz.ma'}

def pathNorm(p):
    return os.path.normpath(p).replace("\\", "/")

class SceneManager():
    def __init__(self, d_inContext=None):
        self.context={}
        self.projectname="zombillenium"
        self.context['damProject'] = damproject.DamProject(self.projectname, libraryType=MrcLibrary)    

        if self.context['damProject'] == None:
            pc.error("Cannot initialize project '{0}'".format(self.projectname))

    def getTasks(self, b_inMyTasks=False):
        filters =   [
                        ['entity', 'is', self.context['entity']],
                        ['step', 'is', self.context['step']]
                    ]

        if b_inMyTasks:
            filters.append(['sg_operators', 'contains', self.context['damProject']._shotgundb.currentUser])

        """
        {
            "filter_operator": "any",
            "filters": [
                [ "sg_status_list", "is", "rdy"],
                [ "sg_status_list", "is", "ip" ]
            ]
        }
        """

        fields = ['content', 'step', 'entity', 'project', 'sg_status_list', 'sg_operators']
        tasks = self.context['damProject']._shotgundb.sg.find("Task", filters, fields)

        return tasks

    def getVersions(self):
        filters =   [
                        ['sg_task', 'is', self.context['task']]
                    ]

        fields = ['code', 'entity', 'sg_task']
        versions = self.context['damProject']._shotgundb.sg.find("Version", filters, fields)

        return versions

    def getPath(self, d_inEntity, s_inFileTag):
        #print 'getPath ' + str(d_inEntity)

        lib = LIBS[d_inEntity['type']]
        tokens = {}

        #print "d_inEntity " + str(d_inEntity)
        nameKey = 'name'

        if d_inEntity['type'] == 'Shot':
            nameKey = 'code'
            tokens['name']=d_inEntity[nameKey]
            tokens['sequence']=d_inEntity['sg_sequence']['name']
        elif d_inEntity['type'] == 'Asset':
            tokens['name']=d_inEntity[nameKey]
            tokens['assetType']=d_inEntity[nameKey].split('_')[0]

        #"public","asset_lib","master_file", tokens={"assetType":"chr","asset":sAssetName}
        #print 'tokens ' + str(tokens)
        path = None
        try:
            path = self.context['damProject'].getPath('public', lib, s_inFileTag, tokens=tokens)
        except Exception, e:
            pc.warning('damProject.getPath failed : {0}'.format(e))

        if path == None:
            path = self.context['damProject'].getPath('public', lib, 'entity_dir', tokens=tokens)
            fileName = None
            
            if d_inEntity['type'] == 'Asset':
                fileName = d_inEntity[nameKey] + FILE_SUFFIXES[self.context['step']['name']]
            elif d_inEntity['type'] == 'Shot':
                fileName = d_inEntity[nameKey] + FILE_SUFFIXES[self.context['step']['name']]

            if 'ref' in s_inFileTag:
                path = os.path.join(path, 'ref')
                fileName = fileName.replace('.ma', '.mb')

            if fileName == None:
                pc.error('Cannot get file name of {0} on {1}'.format(s_inFileTag, d_inEntity))

            path = pathNorm(os.path.join(path, fileName))

        return path

    def getShotgunContent(self):
        #print 'getShotgunContent ' + self.context['entity']['code']
        return self.context['damProject']._shotgundb.getShotAssets(self.context['entity']['code'])

    def getAssetsInfo(self):
        sgAssets = self.getShotgunContent()
        sceneAssets = mop.getSceneContent(self)

        assetsInfo = []

        remainingAssets = list(sceneAssets)

        for assetOccurence in sgAssets:
            occurences = assetOccurence['sg_occurences']
            path = self.getPath(assetOccurence['asset'], 'previz_ref')
            exists = False

            #print '{0} time(s) {1} ({2}) with path {3}'.format(occurences, assetOccurence['asset']['name'], 'previz_ref', path)
            if os.path.isfile(path):
                #print 'Asset found {0} !'.format(assetOccurence['asset']['name'])
                exists = True
            else:
                pc.warning('Asset NOT found {0} !'.format(assetOccurence['asset']['name']))

            dbInfo = assetOccurence['asset']['name']
            if not exists:
                dbInfo += ' ({0})'.format(notFoundvalue)

            localInfo = noneValue
            foundSceneAsset = None
            for sceneAsset in remainingAssets:
                if path == sceneAsset['path']:
                    foundSceneAsset = sceneAsset
                    localInfo = sceneAsset['name']
                    break

            if foundSceneAsset != None:
                remainingAssets.remove(foundSceneAsset)

            assetsInfo.append({'name':assetOccurence['asset']['name'], 'localinfo':localInfo, 'dbinfo':dbInfo, 'path':path})

        for remainingAsset in remainingAssets:
            assetsInfo.append({'name':remainingAsset['name'], 'localinfo':remainingAsset['name'], 'dbinfo':noneValue, 'path':remainingAsset['path']})

        return assetsInfo

    def updateScene(self):
        assetsInfo = self.getAssetsInfo()

        for assetInfo in assetsInfo:
            #print 'assetInfo["dbinfo"] ' + str(assetInfo['dbinfo'])
            #print 'assetInfo["localinfo"] ' + str(assetInfo['localinfo'])
            #print 'assetInfo["path"]' + str(assetInfo['path'])
            if assetInfo['dbinfo'] != noneValue and assetInfo['dbinfo'] != assetInfo['localinfo']:
                if notFoundvalue in assetInfo['dbinfo']:
                    pc.warning('Asset {0} does not exists ({1})'.format(assetInfo['name'], assetInfo['path']))
                else:
                    mop.importAsset(assetInfo['path'])
        
        mop.reArrangeAssets()

    def updateShotgun(self):
        pass

    def do(self, s_inCmd):
        mop.do(s_inCmd, self.context['task']['content'], self)