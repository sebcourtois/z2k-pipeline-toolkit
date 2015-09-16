import pymel.core as pc
import maya.cmds as mc
import tkMayaCore as tkc

import os
import re

from davos.core import damproject
from davos.core.damtypes import DamShot

from davos_maya.core import mrclibrary
MrcLibrary = mrclibrary.MrcLibrary

import dminutes.maya_scene_operations as mop

PROJECTNAME = "zombillenium"

noneValue = 'None !'
notFoundvalue = 'Not found !'

#FROM DAVOS !!!!
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

    #FROM DAVOS !!!!
    def collapseVariables(self, s_inPath, encapsulation="${0}"):
        variables = {}
        for key, lib in self.context['damProject'].loadedLibraries.iteritems():
            variable = lib.getVar('public_path').lstrip("$")
            if not variable in variables:
                variables[variable] = os.environ[variable]

        for key, path in variables.iteritems():
            alternatePath = path.replace("\\", "/")
            if path in s_inPath:
                return s_inPath.replace(path, encapsulation.format(key))
            elif alternatePath in s_inPath:
                return s_inPath.replace(alternatePath, encapsulation.format(key))

                
        return s_inPath

    def getTasks(self, b_inMyTasks=False):
        userOrNone = self.context['damProject']._shotgundb.currentUser if b_inMyTasks else None

        return self.context['damProject']._shotgundb.getTasks(self.context['entity'], self.context['step'], userOrNone)

    def getVersions(self):
        return self.context['damProject']._shotgundb.getVersions(self.context['task'])

    def createFolder(self):
        nameKey = 'name'

        if self.context['entity']['type'] == 'Shot':
            nameKey = 'code'

            damShot = DamShot(self.context['damProject'], name=self.context['entity'][nameKey])
            damShot.createDirsAndFiles()

    def saveIncrement(self, b_inForce=True):
        currentScene = os.path.abspath(mc.file(q=True, sn=True))
        if currentScene == '':
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

        matches = re.match(".*(v\d{3})\.(\d{3})\.ma", currentScene)
        
        if matches:
            curVersion = int(matches.group(2))
            curVersion += 1
            newFileName = '{0}.{1:03}.ma'.format(currentScene.split('.')[0], curVersion)
            if b_inForce or not os.path.isfile(newFileName):
                return pc.saveAs(newFileName)
        else:
            pc.warning("Invalid file pattern !")
        
        return None

    def capture(self):
        global CAPTUREINFO

        savedFile = self.saveIncrement(b_inForce=False)
        if savedFile != None:

            CAPTUREINFO['user'] = self.context['damProject']._shotgundb.currentUser['name']
            #Infer capture path
            scenePath = mc.file(q=True, sn=True)
            CAPTUREINFO['scene'] = os.path.basename(scenePath)

            capturePath = scenePath.replace(".ma", ".mov")

            #Get start/end from shotgun
            captureStart = 101
            CAPTUREINFO['start'] = captureStart
            duration = self.context['entity']['sg_cut_out'] - self.context['entity']['sg_cut_in']
            captureEnd = captureStart + duration
            CAPTUREINFO['end'] = captureEnd

            #get camera
            camName = 'cam_{0}'.format(self.context['entity']['code'])
            cams = pc.ls(camName+":*", type='camera')

            if len(cams) == 0:
                pc.error("Cannot detect camera with pattern {0}".format(camName))

            cam = cams[0].getParent()

            CAPTUREINFO['cam'] = cams[0].name()
            oldValues = createHUD()

            pc.setAttr(cams[0].name() + '.aspectRatio', 1.85)

            #Detect if activePanel is an imageplane and change to 'modelPanel4' if True
            curPanel = pc.playblast(activeEditor=True)
            curCam = pc.modelEditor(curPanel, query=True, camera=True)
            if len(pc.PyNode(curCam).getShape().getChildren() > 0):
                pc.setFocus('modelPanel4')

            tkc.capture(capturePath, captureStart, captureEnd, 1280, 720, "shaded", format="qt", compression="H.264", ornaments=True,
                useCamera='cam_sq6660_sh0010a:cam_shot_default', i_inFilmFit=1, i_inDisplayFilmGate=1,
                i_inSafeAction=1, i_inSafeTitle=0, i_inGateMask=1, f_inMaskOpacity=1.0)

            restoreHUD(oldValues)

            pc.setAttr(cams[0].name() + '.aspectRatio', 1.7778)

    def edit(self, onBase=False):
        privFile = None

        lib = LIBS[self.context['entity']['type']]
        if lib == "asset_lib":
            lib =  self.context['entity']['sg_asset_type']

        tokens = {}

        nameKey = 'name'

        if self.context['entity']['type'] == 'Shot':
            nameKey = 'code'
            tokens['name']=self.context['entity'][nameKey]
            tokens['sequence']=self.context['entity']['sg_sequence']['name']
        elif d_inEntity['type'] == 'Asset':
            tokens['name']=self.context['entity'][nameKey]
            tokens['assetType']=self.context['entity'][nameKey].split('_')[0]

        if 'task' in self.context:
            if self.context['task']['content'] in TASK_FILE_REL:
                s_inFileTag = TASK_FILE_REL[self.context['task']['content']]

                path = None
                try:
                    path = self.context['damProject'].getPath('public', lib, s_inFileTag, tokens=tokens)
                except Exception, e:
                    pc.warning('damProject.getPath failed : {0}'.format(e))

                if path != None:
                    entry = self.context['damProject'].entryFromPath(path)
                    if entry == None:
                        result = pc.confirmDialog( title='Non existing entity', message='Entity does not exists, do yout want to create it ?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No')
                        pc.error("result " + result)
                    
                    privFile = entry.edit(openFile= not onBase, existing='choose')#existing values = choose, fail, keep, abort, overwrite

                    if privFile is None:
                        pc.warning('There was a problem with the edit !')
            else:
                pc.warning('Given task "{0}" is unknown (choose from {1}) !'.format(TASK_FILE_REL.keys()))
        else:
            pc.warning('No task given !')

        return privFile

    def publish(self):
        currentScene = os.path.abspath(mc.file(q=True, sn=True))
        if currentScene != '':
            self.context['damProject'].publishEditedVersion(currentScene)
        else:
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

    def getPath(self, d_inEntity, s_inFileTag):
        #print 'getPath ' + str(d_inEntity)
        #print d_inEntity
        lib = LIBS[d_inEntity['type']]
        if lib == "asset_lib":
            lib = d_inEntity['name'].split("_")[0]

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
            pc.warning('damProject.getPath failed with {0}, {1}, {2} : {3}'.format(lib,s_inFileTag,tokens, e))

        if path == None and False:
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
        content = self.context['damProject']._shotgundb.getShotAssets(self.context['entity']['code'])
        return content if content != None else []

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
                pc.warning('Asset NOT found {0} ({1})!'.format(assetOccurence['asset']['name'], path))

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

    def updateScene(self, addOnly=True):
        assetsInfo = self.getAssetsInfo()

        for assetInfo in assetsInfo:
            #print 'assetInfo["dbinfo"] ' + str(assetInfo['dbinfo'])
            #print 'assetInfo["localinfo"] ' + str(assetInfo['localinfo'])
            #print 'assetInfo["path"]' + str(assetInfo['path'])
            if assetInfo['dbinfo'] == noneValue:
                if not addOnly:
                    #Asset that does not exist in shot, remove
                    mop.removeAsset(self.collapseVariables(assetInfo['path']))
            elif assetInfo['dbinfo'] != assetInfo['localinfo']:
                if notFoundvalue in assetInfo['dbinfo']:
                    pc.warning('Asset {0} does not exists ({1})'.format(assetInfo['name'], assetInfo['path']))
                else:
                    mop.importAsset(self.collapseVariables(assetInfo['path']))
        
        mop.reArrangeAssets()

    def updateShotgun(self, addOnly=True):
        pass

    def do(self, s_inCmd):
        mop.do(s_inCmd, self.context['task']['content'], self)

# capture
CAPTUREINFO = {}

def userInfo():
    return CAPTUREINFO['user']

def sceneInfo():
    return CAPTUREINFO['scene']

def stepInfo():
    return 'Previz 3D'

def frameInfo():
    return pc.currentTime(query=True)
    
def focalInfo():
    return 'F {0}mm'.format(pc.getAttr('{0}.focalLength'.format(CAPTUREINFO['cam'])))
    
def endFrameInfo():
    return CAPTUREINFO['end']

def createHUD():
    headsUps = pc.headsUpDisplay(listHeadsUpDisplays=True)

    headUpsValues = {}
    for headsUp in headsUps:
        headUpsValues[headsUp] = pc.headsUpDisplay(headsUp, query=True, visible=True)
        pc.headsUpDisplay(headsUp, edit=True, visible=False)

    pc.headsUpDisplay( 'HUD_ZOMBUser', section=0, block=pc.headsUpDisplay(nextFreeBlock=0), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=userInfo, attachToRefresh=True)
    pc.headsUpDisplay( 'HUD_ZOMBScene', section=2, block=pc.headsUpDisplay(nextFreeBlock=2), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=sceneInfo, attachToRefresh=True)
    pc.headsUpDisplay( 'HUD_ZOMBStep', section=4, block=pc.headsUpDisplay(nextFreeBlock=4), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=stepInfo, attachToRefresh=True)
    pc.headsUpDisplay( 'HUD_ZOMBFrame', section=5, block=pc.headsUpDisplay(nextFreeBlock=5), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=frameInfo, attachToRefresh=True)
    pc.headsUpDisplay( 'HUD_ZOMBFocal', section=7, block=pc.headsUpDisplay(nextFreeBlock=7), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=focalInfo, attachToRefresh=True)
    pc.headsUpDisplay( 'HUD_ZOMBEndFrame', section=9, block=pc.headsUpDisplay(nextFreeBlock=9), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=endFrameInfo, attachToRefresh=True)

    return headUpsValues

def restoreHUD(oldValues=None):
    pc.headsUpDisplay( 'HUD_ZOMBUser', rem=True)
    pc.headsUpDisplay( 'HUD_ZOMBScene', rem=True)
    pc.headsUpDisplay( 'HUD_ZOMBStep', rem=True)
    pc.headsUpDisplay( 'HUD_ZOMBFrame', rem=True)
    pc.headsUpDisplay( 'HUD_ZOMBFocal', rem=True)
    pc.headsUpDisplay( 'HUD_ZOMBEndFrame', rem=True)

    headsUps = pc.headsUpDisplay(listHeadsUpDisplays=True)

    if oldValues != None:
        for k, v in oldValues.iteritems():
            if k in headsUps:
                pc.headsUpDisplay(k, edit=True, visible=v)