#------------------------------------------------------------------
#               UI data and logic for sceneManagerUI.py
#------------------------------------------------------------------

import pymel.core as pc
import maya.cmds as mc

import tkMayaCore as tkc

import os
import re

from davos.core import damproject
from davos.core.damtypes import DamShot

from davos_maya.core import mrclibrary
from davos.core.utils import versionFromName
MrcLibrary = mrclibrary.MrcLibrary

import dminutes.maya_scene_operations as mop
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
import dminutes.camImpExp as camIE
reload(camIE)
import dminutes.infoSetExp as infoE
reload(infoE)


# get zomb project
PROJECTNAME = os.environ.get("DAVOS_INIT_PROJECT")

noneValue = 'NONE'
notFoundvalue = 'NOT FOUND'

#FROM DAVOS !!!!
STEP_FILE_REL = {'Previz 3D':'previz_scene'}
TASK_FILE_REL = {'previz 3D':'previz_scene'}
TASK_ASSET_REL = {'previz 3D':'previz_ref', 'animation':'anim_ref'}

LIBS = {'Asset':'asset_lib', 'Shot':'shot_lib'}

FILE_SUFFIXES = {'Previz 3D':'_previz.ma'}



def getReversedDict(in_dict):
    """Get a copy of a dictionary key<=>value (Beware of identical values)"""
    reverseDict = {}

    for key in in_dict:
        if not in_dict[key] in reverseDict:
            reverseDict[in_dict[key]] = key

    return reverseDict

def pathNorm(p):
    """Normalize a path, in term of separator"""
    return os.path.normpath(p).replace("\\", "/")

class SceneManager():
    """Main Class to handle SceneManager Data and operations"""
    def __init__(self, d_inContext=None):
        self.context={}
        self.projectname="zombillenium"
        self.context['damProject'] = damproject.DamProject(self.projectname, libraryType=MrcLibrary)

        if self.context['damProject'] == None:
            pc.error("Cannot initialize project '{0}'".format(self.projectname))

    #FROM DAVOS !!!!
    def collapseVariables(self, s_inPath, encapsulation="${0}"):
        """Format a path with environment variables visible (for asset referencing for instance)"""
        variables = {}
        for key, lib in self.context['damProject'].loadedLibraries.iteritems():
            variable = lib.getVar('public_path').lstrip("$")
            if not variable in variables:
                print "variable=", variable
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

    def getPath(self, d_inEntity, s_inFileTag):
        """Get the path of an asset (for referencing), s_inFileTag stands for the 'ressource' in davos config (previz_scene, previz_ref...etc)"""

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

        """
        #This part was usefull when davos was not completely configured, should be pointless now
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
        """

        return path

    def getContextFromDavosData(self):
        """format davos data (contained in self.context['sceneData']) to match with UI Data to allow detection of current loaded scene"""
        davosContext = {}
        if not "resource" in self.context['sceneData'] or not "section" in self.context['sceneData'] or not "name" in self.context['sceneData']:
            return None

        if self.context['sceneData']["section"] == "shot_lib":
            file_step_rel = getReversedDict(STEP_FILE_REL)
            if self.context['sceneData']["resource"] in file_step_rel:
                davosContext['step'] = file_step_rel[self.context['sceneData']["resource"]]

            davosContext['seq'] = self.context['sceneData']["sequence"]
            davosContext['shot'] = self.context['sceneData']["name"]

        elif self.context['sceneData']["section"] == "asset_lib":
            pc.warning("asset_lib section not managed yet !!")
            return None
        else:
            pc.warning("Unknown section {0}".format(self.context['sceneData']["section"]))
            return None

        return davosContext

    def refreshSceneContext(self):
        """Retrieve the scene path and get davos data from it"""
        self.context['sceneEntry'] = None
        self.context['sceneData'] = {}

        curScenePath = os.path.abspath(mc.file(q=True, sn=True))
        if curScenePath != '':
            entry = self.context['damProject'].entryFromPath(curScenePath)
            if entry != None:
                self.context['sceneEntry'] = entry
                self.context['sceneData'] = self.context['damProject'].dataFromPath(curScenePath)

        return self.contextIsMatching()

    def contextIsMatching(self):
        """Compare davos data with UI data, return True if they match"""
        self.context['sceneState'] = ""
        contextEntry = self.getEntry()

        if contextEntry == None or self.context['sceneEntry'] == None:
            self.context['sceneState'] = "Cannot autodetect context !"
            return False

        sceneEntryPath = self.context['sceneEntry'].getPublicFile().absPath()
        if contextEntry.absPath() == sceneEntryPath:
            iSrcVers = versionFromName(self.context['sceneEntry'].name)
            iNxtVers = contextEntry.currentVersion + 1

            if iSrcVers < iNxtVers:
                self.context['sceneState'] = "Current scene version is obsolete ({0} => {1}) !".format(iSrcVers, iNxtVers)
                return False

            return True

        self.context['sceneState'] = "Your context does not match with current scene ({0} => {1}) !".format(os.path.basename(contextEntry.absPath()), os.path.basename(sceneEntryPath))
        return False

    def isEditable(self):
        if self.context['lock'] != "Error":
            return self.context['lock'] == "" or self.context['lock'] == self.context['damProject']._shotgundb.currentUser['login']

        return False

    def assert_isEditable(self):
        message = ""
        
        if not self.refreshSceneContext():
            message = self.context['sceneState']
        
        if not self.isEditable():
            message = "Your entity is locked by {0} !".format(self.context['lock'])

        if message != "":
            pc.confirmDialog(title='Entity not editable', message=message, button=['Ok'])
            return False

        return True

    def refreshStatus(self, entry=None):
        """Refresh the 'lock' status"""
        self.context['lock'] = "Error"

        if entry == None:
            entry = self.getEntry()

        if entry != None:
            self.context['lock'] = entry.getLockOwner()

    def getEntry(self):
        """Get davos entry from UI data"""
        entry = None

        lib = LIBS[self.context['entity']['type']]
        if lib == "asset_lib":
            lib =  self.context['entity']['sg_asset_type']

        tokens = {}

        nameKey = 'code'

        if self.context['entity']['type'] == 'Shot':
            tokens['name']=self.context['entity'][nameKey]
            tokens['sequence']=self.context['entity']['sg_sequence']['name']
        elif self.context['entity']['type'] == 'Asset':
            print self.context['entity']
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

        return entry

    def createFolder(self):
        nameKey = 'name'

        if self.context['entity']['type'] == 'Shot':
            nameKey = 'code'

            damShot = DamShot(self.context['damProject'], name=self.context['entity'][nameKey])
            damShot.createDirsAndFiles()

    def save(self, b_inForce=True):
        entry = self.getEntry()

        if entry == None:
            pc.error("Cannot get entry for context {0}".format(self.context))

        currentScene = os.path.abspath(mc.file(q=True, sn=True))
        if currentScene == '':
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

        return pc.saveAs(currentScene, force=b_inForce)

    # def saveIncrement(self, b_inForce=True):
    #     # old 
    #     entry = self.getEntry()

    #     if entry == None:
    #         pc.error("Cannot get entry for context {0}".format(self.context))

    #     currentScene = os.path.abspath(mc.file(q=True, sn=True))
    #     if currentScene == '':
    #         pc.error("Please save your scene as a valid private working scene (Edit if needed)")

    #     matches = re.match(".*(v\d{3})\.(\d{3})\.ma", currentScene)
        
    #     if matches:
    #         curVersion = int(matches.group(2))
    #         curVersion += 1
    #         newFileName = '{0}.{1:03}.ma'.format(currentScene.split('.')[0], curVersion)
    #         if b_inForce or not os.path.isfile(newFileName):
    #             return pc.saveAs(newFileName, force=b_inForce)
    #         else:
    #             pc.error("File already exists ({0})!".format(newFileName))
    #     else:
    #         pc.warning("Invalid file pattern !")
        
    #     return None

    def saveIncrement(self, b_inForce=True):
        # new incrementing system based on the last versoin present in the folder 
        entry = self.getEntry()

        if entry == None:
            pc.error("Cannot get entry for context {0}".format(self.context))

        currentScene = os.path.abspath(mc.file(q=True, sn=True))
        if currentScene == '':
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

        matches = re.match(".*(v\d{3})\.(\d{3})\.ma", currentScene)
        
        if matches:
            print "currentScene=", currentScene
            newFileName = jpZ.createIncrementedFilePath(filePath=currentScene,vSep= ".", extSep=".ma", digits=3,)

            if b_inForce or not os.path.isfile(newFileName):
                return pc.saveAs(newFileName, force=b_inForce)
            else:
                pc.error("File already exists ({0})!".format(newFileName))
        else:
            pc.warning("Invalid file pattern !")
        
        return None


    def capture(self, increment=True):
        # BUG pas de son alors que son present dans la scene
        # BUG first frame decalee dupliquee dans les fichier output
        global CAPTUREINFO

        savedFile = None

        if increment:
            savedFile = self.saveIncrement(b_inForce=False)
        else:
            savedFile = self.save(b_inForce=False)

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
            if len(pc.PyNode(curCam).getShape().getChildren()) > 0:
                pc.setFocus('modelPanel4')

            tkc.capture(capturePath, captureStart, captureEnd, 1280, 720, "shaded", format="qt", compression="H.264", ornaments=True,
                useCamera=cam, i_inFilmFit=1, i_inDisplayFilmGate=1, i_inSafeAction=1, i_inSafeTitle=0, i_inGateMask=1, f_inMaskOpacity=1.0, play=True)

            restoreHUD(oldValues)

            pc.setAttr(cams[0].name() + '.aspectRatio', 1.7778)

            os.system("start "+capturePath.replace("/", "\\"))

    def edit(self, editInPlace=None, onBase=False):
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
                        result = pc.confirmDialog( title='Non existing entity', message='Entity "{0}"" does not exists, do yout want to create it ?'.format(self.context['entity'][nameKey]), button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No')
                        if result == "Yes":
                            self.createFolder()
                            entry = self.context['damProject'].entryFromPath(path)
                            if entry == None:
                                pc.error("Problem editing the entity !")
                        else:
                            pc.warning('Edit cancelled by user !')
                            return ''
                    
                    result = "Yes" if editInPlace else "No"

                    if editInPlace == None:
                        result = pc.confirmDialog( title='Edit options', message='Do you want to use current scene for this edit ?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No')

                    if result == "Yes":
                        privFile = entry.edit(openFile=False, existing="keep")#existing values = choose, fail, keep, abort, overwrite

                        rootPath, filename = os.path.split(privFile.absPath())
                        vSplit = filename.split('.')
                        if len(vSplit) != 3:
                            pc.error("Unrecognized file pattern ! {0}".format(filename))

                        version = vSplit[1]
                        elements = os.listdir(rootPath)

                        for element in elements:
                            fullpath = os.path.join(rootPath, element)
                            if vSplit[0] in element and os.path.isfile(fullpath):
                                dSplit = element.split('.')
                                if len(dSplit) == 3 and dSplit[1] > version:
                                    version = dSplit[1]

                        iversion = int(version) + 1

                        newpath = os.path.join(rootPath, vSplit[0] + ".{0:03}.ma".format(iversion))
                        mc.file(rename=newpath)
                        mc.file(save=True)
                    else:
                        privFile = entry.edit(openFile= not onBase, existing='choose')#existing values = choose, fail, keep, abort, overwrite

                    if privFile is None:
                        pc.warning('There was a problem with the edit !')
                    else:
                        pass
                        #print "privFile " + str(privFile.absPath())
            else:
                pc.warning('Given task "{0}" is unknown (choose from {1}) !'.format(TASK_FILE_REL.keys()))
        else:
            pc.warning('No task given !')

        return privFile

    def publish(self):
        currentScene = os.path.abspath(mc.file(q=True, sn=True))
        if currentScene != '':
            entry = self.context['damProject'].entryFromPath(currentScene)
            if entry == None:
                pc.error()

            rslt = self.context['damProject'].publishEditedVersion(currentScene)

            # here is incerted the publish of the camera of the scene
            print "exporting the camera of the shot"
            camImpExpI = camIE.camImpExp()
            camImpExpI.exportCam (sceneName=jpZ.getShotName(), )

            # here is the publish of the infoSet file with the position of the global and local srt of sets assets
            infoSetExpI =infoE.infoSetExp()
            infoSetExpI.export(sceneName=jpZ.getShotName())

            # here is the original publish
            if rslt != None:
                pc.confirmDialog( title='Publish OK', message='{0} was published successfully'.format(rslt[0].name))
        else:
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

    def getShotgunContent(self):
        #print 'getShotgunContent ' + self.context['entity']['code']
        content = self.context['damProject']._shotgundb.getShotAssets(self.context['entity']['code'])
        return content if content != None else []

    def getFiletagFromPath(self, in_sPath):
        """Detect the filetag (resource) from an asset path, when we don't have the shotgun info, right now it'll just say 'NONE'"""
        return notFoundvalue

    def getAssetsInfo(self):
        """Compare Shotgun shot<=>assets linking and scene content"""
        sgAssets = self.getShotgunContent()
        sceneAssets = mop.getSceneContent(self)

        assetsInfo = []

        remainingAssets = list(sceneAssets)

        #consider previz_ref as default
        fileTag = "previz_ref"

        if self.context['task']['content'] in TASK_ASSET_REL:
            fileTag = TASK_ASSET_REL[self.context['task']['content']]
        else:
            pc.warning('Cannot detect file tag from task {0}, {1} used by default !!'.format(self.context['task']['content'], fileTag))

        for assetOccurence in sgAssets:
            occurences = assetOccurence['sg_occurences']
            path = self.getPath(assetOccurence['asset'], fileTag)
            exists = False
            print "*path=", path
            print '{0} time(s) {1} ({2}) with path {3}'.format(occurences, assetOccurence['asset']['name'], fileTag, path)
            if path:
                if os.path.isfile(path):
                    #print 'Asset found {0} !'.format(assetOccurence['asset']['name'])
                    exists = True
                else:
                    pc.warning('Asset NOT found {0} ({1})!'.format(assetOccurence['asset']['name'], path))

                dbInfo = assetOccurence['asset']['name']
                if not exists:
                    dbInfo += ' ({0})'.format(notFoundvalue)
                else:
                    dbInfo += " ("+fileTag+")"

                localInfo = noneValue
                foundSceneAsset = None
                for sceneAsset in remainingAssets:
                    if path == sceneAsset['path']:
                        foundSceneAsset = sceneAsset
                        localInfo = sceneAsset['name'] + " ("+fileTag+")"
                        break

                if foundSceneAsset != None:
                    remainingAssets.remove(foundSceneAsset)

                assetsInfo.append({'name':assetOccurence['asset']['name'], 'localinfo':localInfo, 'dbinfo':dbInfo, 'path':path})
            
            else:
                pc.warning('PATH= NONE  -> Asset NOT found {0} ({1})!'.format(assetOccurence['asset']['name'], path))

        for remainingAsset in remainingAssets:
            assetFullName = remainingAsset['name'] + " ("+self.getFiletagFromPath(remainingAsset['path'])+")"
            assetsInfo.append({'name':remainingAsset['name'], 'localinfo':assetFullName, 'dbinfo':noneValue, 'path':remainingAsset['path']})

        return assetsInfo

    # BASE FUNCTION (NOT WORKING)
    # def updateScene(self, addOnly=True):
    #     """Updates scene Assets from shotgun shot<=>assets linking"""
    #     assetsInfo = self.getAssetsInfo()

    #     for assetInfo in assetsInfo:
    #         #print 'assetInfo["dbinfo"] ' + str(assetInfo['dbinfo'])
    #         #print 'assetInfo["localinfo"] ' + str(assetInfo['localinfo'])
    #         #print 'assetInfo["path"]' + str(assetInfo['path'])
    #         if assetInfo['dbinfo'] == noneValue:
    #             if not addOnly:
    #                 #Asset that does not exist in shot, remove
    #                 mop.removeAsset(self.collapseVariables(assetInfo['path']))
    #         elif assetInfo['dbinfo'] != assetInfo['localinfo']:
    #             if notFoundvalue in assetInfo['dbinfo']:
    #                 pc.warning('Asset {0} does not exists ({1})'.format(assetInfo['name'], assetInfo['path']))
    #             else:
    #                 mop.importAsset(self.collapseVariables(assetInfo['path']), assetInfo['name'] + "_1")
        
    #     mop.reArrangeAssets()

    def updateScene(self, addOnly=True):
        """Updates scene Assets from shotgun shot<=>assets linking"""
        # WIP CORRECTION collapseVariables (ERROR)
        assetsInfo = self.getAssetsInfo()

        for assetInfo in assetsInfo:
            # print '**          assetInfo["dbinfo"] ' + str(assetInfo['dbinfo'])
            # print '**          assetInfo["localinfo"] ' + str(assetInfo['localinfo'])
            # print '**          assetInfo["path"]' + str(assetInfo['path'])

            # get_File_By_DAVOS methodes
            drcFile = self.context["damProject"].entryFromPath(assetInfo['path'])
            The_ASSET_PATH = drcFile.envPath()
            # print "* The_ASSET_PATH=", The_ASSET_PATH
            if assetInfo['dbinfo'] == noneValue:
                if not addOnly:
                    #Asset that does not exist in shot, remove
                    mop.removeAsset(The_ASSET_PATH)
            elif assetInfo['dbinfo'] != assetInfo['localinfo']:
                if notFoundvalue in assetInfo['dbinfo']:
                    pc.warning('Asset {0} does not exists ({1})'.format(assetInfo['name'], assetInfo['path']))
                else:
                    mop.importAsset(The_ASSET_PATH, assetInfo['name'] + "_1")
        
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
    deleteHUD()
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


def deleteHUD(*args, **kwargs):
    # FUNCTION QUI SEMBLE MANQUER, a ajouter quelque part apres le playblast
    # actuellement il y a un bug qui fait que t'as des script qui tournent en permanence dans la scene, et qui plante si
    # ce n'est pas une scene zombie avec une belle camera
    headsUps = mc.headsUpDisplay(listHeadsUpDisplays=True)
    for i in headsUps:
        if "HUD_ZOMB" in i:
            print i
            mc.headsUpDisplay(i,rem=True)


