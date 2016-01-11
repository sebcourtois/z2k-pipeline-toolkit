#------------------------------------------------------------------
#               UI data and logic for sceneManagerUI.py
#------------------------------------------------------------------

import os
import re
from collections import OrderedDict

import pymel.core as pc
import maya.cmds as cmds
import maya.mel

#import tkMayaCore as tkc
from pytd.util.fsutils import pathResolve, normCase
from pytd.util.logutils import logMsg

from davos.core import damproject
from davos.core.damtypes import DamShot, DamAsset
from davos.core.utils import versionFromName

from zomblib import shotgunengine

import dminutes.maya_scene_operations as mop
import dminutes.jipeLib_Z2K as jpZ
import dminutes.camImpExp as camIE
import dminutes.infoSetExp as infoE

reload(jpZ)
reload(camIE)
reload(infoE)

# get zomb project
PROJECTNAME = os.environ.get("DAVOS_INIT_PROJECT")

okValue = 'OK'
noneValue = 'MISSING'
notFoundvalue = 'NOT FOUND'

#FROM DAVOS !!!!
STEP_FILE_REL = {'Previz 3D':'previz_scene', 'Layout':'layout_scene'}
TASK_FILE_REL = {'previz 3D':'previz_scene', 'layout':'layout_scene'}
REF_FOR_TASK = {'previz 3D':'previz_ref', 'layout':'anim_ref', 'animation':'anim_ref'}

LIBS = {'Asset':'asset_lib', 'Shot':'shot_lib'}


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

def restoreSelection(func):

    def doIt(*args, **kwargs):

        sSelList = cmds.ls(sl=True)
        try:
            ret = func(*args, **kwargs)
        finally:
            if sSelList:
                try:
                    cmds.select(sSelList)
                except Exception as e:
                    print "Could restore previous selection: {}".format(e)

        return ret
    return doIt

@restoreSelection
def makeCapture(filepath, start, end, width, height, displaymode="",
                showFrameNumbers=True, format="iff", compression="jpg",
                ornaments=False, play=False, useCamera=None, audioNode=None,
                i_inFilmFit=0, i_inDisplayResolution=0, i_inDisplayFilmGate=0,
                i_inOverscan=1.0, i_inSafeAction=0, i_inSafeTitle=0,
                i_inGateMask=0, f_inMaskOpacity=0.8):

    pc.select(cl=True)
    names = []
    name = ""

    pan = pc.playblast(activeEditor=True)
    app = pc.modelEditor(pan, query=True, displayAppearance=True)
    tex = pc.modelEditor(pan, query=True, displayTextures=True)
    wireOnShaded = pc.modelEditor(pan, query=True, wireframeOnShaded=True)
    xray = pc.modelEditor(pan, query=True, xray=True)
    jointXray = pc.modelEditor(pan, query=True, jointXray=True)
    hud = pc.modelEditor(pan, query=True, hud=True)

    #Camera settings
    oldCamera = None
    if useCamera != None:
        curCam = pc.modelEditor(pan, query=True, camera=True)
        if curCam != useCamera:
            oldCamera = curCam
            pc.modelEditor(pan, edit=True, camera=useCamera)

    camera = pc.modelEditor(pan, query=True, camera=True)
    if camera.type() == "transform":
        camera = camera.getShape()

    filmFit = pc.getAttr(camera + ".filmFit")
    displayResolution = pc.getAttr(camera + ".displayResolution")
    displayFilmGate = pc.getAttr(camera + ".displayFilmGate")
    overscan = pc.getAttr(camera + ".overscan")
    safeAction = pc.getAttr(camera + ".displaySafeAction")
    safeTitle = pc.getAttr(camera + ".displaySafeTitle")
    displayGateMask = pc.getAttr(camera + ".displayGateMask")
    displayGateMaskOpacity = pc.getAttr(camera + ".displayGateMaskOpacity")

    pc.setAttr(camera + ".filmFit", i_inFilmFit)
    pc.setAttr(camera + ".displayResolution", i_inDisplayResolution)
    pc.setAttr(camera + ".displayFilmGate", i_inDisplayFilmGate)
    pc.setAttr(camera + ".overscan", i_inOverscan)
    pc.setAttr(camera + ".displaySafeAction", i_inSafeAction)
    pc.setAttr(camera + ".displaySafeTitle", i_inSafeTitle)
    pc.setAttr(camera + ".displayGateMask", i_inGateMask)
    pc.setAttr(camera + ".displayGateMaskOpacity", f_inMaskOpacity)

    #visible types
    nurbsCurvesShowing = pc.modelEditor(pan, query=True, nurbsCurves=True)

    editorKwargs = {}
    if displaymode:
        if displaymode == "wireframe":
            pc.modelEditor(pan, edit=True, displayAppearance="wireframe", wireframeOnShaded=False, hud=ornaments)
        else:
            pc.modelEditor(pan, edit=True, displayAppearance="smoothShaded", wireframeOnShaded=False, hud=ornaments)

        editorKwargs = dict(displayTextures="textured" in displaymode or displaymode == "OpenGL")

    pc.modelEditor(pan, edit=True, nurbsCurves=False, **editorKwargs)

    playblastKwargs = dict(format=format, compression=compression, quality=90,
                           sequenceTime=False, clearCache=True, viewer=play,
                           showOrnaments=ornaments,
                           framePadding=4,
                           forceOverwrite=True,
                           percent=100,
                           startTime=start, endTime=end,
                           width=width, height=height,
                           )

    sAudioNode = audioNode
    if not sAudioNode:
        gPlayBackSlider = maya.mel.eval('$tmpVar=$gPlayBackSlider')
        sAudioNode = cmds.timeControl(gPlayBackSlider, q=True, sound=True)

    if sAudioNode:
        sSoundPath = cmds.getAttr(".".join((sAudioNode, "filename")))
        if not os.path.exists(sSoundPath):
            pc.displayError("File of '{}' node not found: '{}' !"
                              .format(sAudioNode, sSoundPath))
        else:
            playblastKwargs.update(sound=sAudioNode)


    if format == "iff" and showFrameNumbers:
        name = pc.playblast(filename=filepath, **playblastKwargs)

        for i in range(start, end + 1):
            oldFileName = name.replace("####", str(i).zfill(4))
            newFileName = oldFileName.replace(".", "_", 1)
            if os.path.isfile(newFileName):
                os.remove(newFileName)
            os.rename(oldFileName, newFileName)
            names.append(newFileName)
    else:
        if format == "iff":
            name = pc.playblast(completeFilename=filepath, **playblastKwargs)
        else:
            name = pc.playblast(filename=filepath, **playblastKwargs)

        names.append(name)

    #Reset values
    pc.modelEditor(pan, edit=True, displayAppearance=app,
                   displayTextures=tex,
                   wireframeOnShaded=wireOnShaded,
                   xray=xray,
                   jointXray=jointXray,
                   nurbsCurves=nurbsCurvesShowing,
                   hud=hud)

    #Camera
    pc.setAttr(camera + ".filmFit", filmFit)
    pc.setAttr(camera + ".displayResolution", displayResolution)
    pc.setAttr(camera + ".displayFilmGate", displayFilmGate)
    pc.setAttr(camera + ".overscan", overscan)
    pc.setAttr(camera + ".displaySafeAction", safeAction)
    pc.setAttr(camera + ".displaySafeTitle", safeTitle)
    pc.setAttr(camera + ".displayGateMask", displayGateMask)
    pc.setAttr(camera + ".displayGateMaskOpacity", displayGateMaskOpacity)

    if oldCamera != None:
        pc.modelEditor(pan, edit=True, camera=oldCamera)

    return names

class SceneManager():
    """Main Class to handle SceneManager Data and operations"""
    def __init__(self, d_inContext=None):
        self.context = {}
        self.projectname = "zombillenium"
        self.context['damProject'] = damproject.DamProject(self.projectname)

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
            tokens['name'] = d_inEntity[nameKey]
            tokens['sequence'] = d_inEntity['sg_sequence']['name']
        elif d_inEntity['type'] == 'Asset':
            tokens['name'] = d_inEntity[nameKey]
            tokens['assetType'] = d_inEntity[nameKey].split('_')[0]

        #"public","asset_lib","master_file", tokens={"assetType":"chr","asset":sAssetName}
        #print 'tokens ' + str(tokens)
        path = None
        try:
            path = self.context['damProject'].getPath('public', lib, s_inFileTag, tokens=tokens)
        except Exception, e:
            pc.warning('damProject.getPath failed with {0}, {1}, {2} : {3}'.format(lib, s_inFileTag, tokens, e))

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
        proj = self.context['damProject']

        curScenePath = pc.sceneName()
        if curScenePath:
            curScenePath = os.path.abspath(curScenePath)
            entry = proj.entryFromPath(curScenePath)
            if entry != None:
                self.context['sceneEntry'] = entry
                self.context['sceneData'] = proj.dataFromPath(curScenePath)

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
            lib = self.context['entity']['sg_asset_type']

        tokens = {}

        nameKey = 'code'

        if self.context['entity']['type'] == 'Shot':
            tokens['name'] = self.context['entity'][nameKey]
            tokens['sequence'] = self.context['entity']['sg_sequence']['name']
        elif self.context['entity']['type'] == 'Asset':
            print self.context['entity']
            tokens['name'] = self.context['entity'][nameKey]
            tokens['assetType'] = self.context['entity'][nameKey].split('_')[0]

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

        currentScene = os.path.abspath(pc.sceneName())
        if currentScene == '':
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

        return pc.saveAs(currentScene, force=b_inForce)

    # def saveIncrement(self, b_inForce=True):
    #     # old
    #     entry = self.getEntry()

    #     if entry == None:
    #         pc.error("Cannot get entry for context {0}".format(self.context))

    #     currentScene = os.path.abspath(pc.sceneName())
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

        currentScene = os.path.abspath(pc.sceneName())
        if currentScene == '':
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

        matches = re.match(".*(v\d{3})\.(\d{3})\.ma", currentScene)

        if matches:
            print "currentScene=", currentScene
            newFileName = jpZ.createIncrementedFilePath(filePath=currentScene, vSep=".", extSep=".ma", digits=3,)

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
            scenePath = pc.sceneName()
            CAPTUREINFO['scene'] = os.path.basename(scenePath)

            capturePath = scenePath.replace(".ma", ".mov")

            #Get start/end from shotgun
            captureStart = 101
            CAPTUREINFO['start'] = captureStart
            duration = self.getDuration()
            captureEnd = captureStart + duration - 1
            CAPTUREINFO['end'] = captureEnd

            #get camera
            camName = 'cam_{0}'.format(self.context['entity']['code'])
            cams = pc.ls(camName + ":*", type='camera')

            if len(cams) == 0:
                pc.error("Cannot detect camera with pattern {0}".format(camName))

            cam = cams[0].getParent()

            CAPTUREINFO['cam'] = cams[0].name()
            oldValues = createHUD()

            pc.setAttr(cams[0].name() + '.aspectRatio', 1.85)

            #Detect if activePanel is an imageplane and change to 'modelPanel4' if True
            curPanel = pc.playblast(activeEditor=True)
            curCam = pc.modelEditor(curPanel, query=True, camera=True)
            if curCam:
                if curCam.type() == "transform":
                    curCam = curCam.getShape()
                if len(curCam.getChildren()) > 0:
                    pc.setFocus('modelPanel4')

            makeCapture(capturePath, captureStart, captureEnd, 1280, 720, useCamera=cam,
                        format="qt", compression="H.264", ornaments=True, play=True,
                        i_inFilmFit=1, i_inDisplayFilmGate=1, i_inSafeAction=1,
                        i_inSafeTitle=0, i_inGateMask=1, f_inMaskOpacity=1.0)

            restoreHUD(oldValues)

            pc.setAttr(cams[0].name() + '.aspectRatio', 1.7778)

            os.system("start " + capturePath.replace("/", "\\"))

    def edit(self, editInPlace=None, onBase=False, createFolders=False):
        privFile = None

        entity = self.context['entity']
        proj = self.context['damProject']

        lib = LIBS[entity['type']]
        if lib == "asset_lib":
            lib = entity['sg_asset_type']

        tokens = {}

        nameKey = 'name'

        if entity['type'] == 'Shot':
            nameKey = 'code'
            tokens['name'] = entity[nameKey]
            tokens['sequence'] = entity['sg_sequence']['name']
        elif entity['type'] == 'Asset':
            tokens['name'] = entity[nameKey]
            tokens['assetType'] = entity[nameKey].split('_')[0]

        if 'task' in self.context:
            sgTask = self.context['task']
            if sgTask['content'] in TASK_FILE_REL:
                s_inFileTag = TASK_FILE_REL[sgTask['content']]

                path = None
                try:
                    path = proj.getPath('public', lib, s_inFileTag, tokens=tokens)
                except Exception, e:
                    pc.warning('damProject.getPath failed : {0}'.format(e))

                if path != None:
                    entry = proj.entryFromPath(path)
                    if not entry:
                        if createFolders:
                            msg = "Entity '{0}' does not exists, do yout want to create it ?".format(entity[nameKey])
                            result = pc.confirmDialog(title='Non existing entity',
                                                      message=msg,
                                                      button=['Yes', 'No'],
                                                      defaultButton='Yes',
                                                      cancelButton='No',
                                                      dismissString='No')
                            if result == "Yes":
                                self.createFolder()
                                entry = proj.entryFromPath(path)
                                if entry == None:
                                    pc.error("Problem editing the entity !")
                            else:
                                pc.warning('Edit cancelled by user !')
                                return ''
                        else:
                            sMsg = "No such file: '{}'".format(path)
                            pc.confirmDialog(title='SORRY !',
                                             message=sMsg,
                                             button=["OK"],
                                             icon="critical",
                                            )
                            raise EnvironmentError(sMsg)

                    result = "Yes" if editInPlace else "No"

                    if editInPlace == None:
                        result = pc.confirmDialog(title='Edit options',
                                                  message='Do you want to use current scene for this edit ?',
                                                  button=['Yes', 'No'],
                                                  defaultButton='Yes',
                                                  cancelButton='No',
                                                  dismissString='No')

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
                        cmds.file(rename=newpath)
                        cmds.file(save=True)
                    else:
                        privFile = entry.edit(openFile=not onBase, existing='choose')#existing values = choose, fail, keep, abort, overwrite

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

        proj = self.context['damProject']

        currentScene = os.path.abspath(pc.sceneName())
        if currentScene != '':
            entry = proj.entryFromPath(currentScene)
            if entry == None:
                pc.error()

            rslt = proj.publishEditedVersion(currentScene)

            # here is incerted the publish of the camera of the scene
            print "exporting the camera of the shot"
            camImpExpI = camIE.camImpExp()
            camImpExpI.exportCam(sceneName=jpZ.getShotName())

            # here is the publish of the infoSet file with the position of the global and local srt of sets assets
            infoSetExpI = infoE.infoSetExp()
            infoSetExpI.export(sceneName=jpZ.getShotName())

            # here is the original publish
            if rslt != None:
                pc.confirmDialog(title='Publish OK', message='{0} was published successfully'.format(rslt[0].name))
        else:
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

    def getShotgunContent(self):
        #print 'getShotgunContent ' + self.context['entity']['code']
        content = self.context['damProject']._shotgundb.getShotAssets(self.context['entity']['code'])
        return content if content != None else []

    def getFiletagFromPath(self, in_sPath):
        """Detect the filetag (resource) from an asset path, when we don't have the shotgun info, right now it'll just say 'NONE'"""
        return notFoundvalue

    def listAssetData(self):
        """Compare Shotgun shot<=>assets linking and scene content"""
        logMsg(log='all')

        sgAstShotConns = self.getShotgunContent()
        assetShotConnDct = dict((d['asset']['name'], d) for d in sgAstShotConns)

        assetDataList = []

        proj = self.context['damProject']
        astLib = proj.getLibrary("public", "asset_lib")

        initData = {'name':'',
                    'sg_info':noneValue,
                    'sg_asset_shot_conn':None,
                    'resource':noneValue,
                    'path':"",
                    'maya_refs':{},
                    'file_refs':[],
                    'occurences':0 }

        sFoundAstList = []
        oFileRefDct = {}
        for oFileRef in pc.iterReferences():

            sRefPath = pathResolve(oFileRef.path)

            sRefNormPath = normCase(sRefPath)
            if sRefNormPath in oFileRefDct:
                oFileRefDct[sRefNormPath].append(oFileRef)
                continue
            else:
                oFileRefDct[sRefNormPath] = [oFileRef]

            pathData = proj.dataFromPath(sRefPath, library=astLib)

            astData = initData.copy()
            astData.update(path=sRefPath, file_refs=oFileRefDct[sRefNormPath])

            if not pathData:
                assetDataList.append(astData)
                continue

            astData.update(pathData)

            sAstName = astData["name"]
            if sAstName in assetShotConnDct:
                astData.update(sg_info=okValue, sg_asset_shot_conn=assetShotConnDct[sAstName])
                sFoundAstList.append(sAstName)

            assetDataList.append(astData)

        for sAstName, astShotConn in assetShotConnDct.iteritems():
            if sAstName not in sFoundAstList:
                astData = initData.copy()
                astData.update(name=sAstName, sg_info=okValue, sg_asset_shot_conn=astShotConn)
                assetDataList.append(astData)

        for astData in assetDataList:

            sAstName = astData['name']
            if not sAstName:
                continue

            damAst = DamAsset(proj, name=sAstName)
            astRcDct = {}

            for sRcName, sRcPath in damAst.iterMayaRcItems(filter="*_ref"):

                mrcFile = proj.entryFromPath(sRcPath, library=damAst.getLibrary(),
                                             dbNode=False)

                rcDct = {"drc_file":mrcFile, "status":okValue}
                astRcDct[sRcName] = rcDct

                if not mrcFile:
                    sMsg = noneValue
                    rcDct["status"] = sMsg
                    continue

                cachedDbNode = mrcFile.getDbNode(fromDb=False)
                if cachedDbNode:
                    mrcFile.refresh(simple=True)
                else:
                    mrcFile.getDbNode(fromCache=False)

                if not mrcFile.currentVersion:
                    sMsg = "NO VERSION"
                    rcDct["status"] = sMsg
                    continue

                if not mrcFile.isUpToDate(refresh=False):
                    sMsg = "OUT OF SYNC"
                    rcDct["status"] = sMsg
                    continue

            astData["maya_refs"] = astRcDct
            astData["occurences"] = len(astData["file_refs"])

        return assetDataList

    def updateScene(self, addOnly=True):
        """Updates scene Assets from shotgun shot<=>assets linking"""

        sgEntity = self.context["entity"]
        if sgEntity["type"].lower() != "shot":
            raise NotImplementedError("Only applies to shots.")

        # WIP CORRECTION collapseVariables (ERROR)
        assetDataList = self.listAssetData()
        errorL = []
        sCurRefTag = self.getCurrentTaskRefTag()

        count = 0
        for astData in assetDataList:
            # print '**          astData["sg_info"] ' + str(astData['sg_info'])
            # print '**          astData["scn_info"] ' + str(astData['scn_info'])
            # print '**          astData["path"]' + str(astData['path'])

            if astData["resource"] != noneValue:
                continue

            try:
                # get_File_By_DAVOS methodes
                rcData = astData["maya_refs"].get(sCurRefTag)
                if not rcData:
                    continue

                sStatus = rcData["status"]
                if sStatus != okValue:
                    raise AssertionError("'{}' is {}".format(sCurRefTag, sStatus))

                mrcFile = rcData["drc_file"]
                mrcFile.mayaImportScene()

            except Exception, err:
                errorTxt = "{0}: {1}".format(astData['name'], err)
                print errorTxt
                errorL.append(errorTxt)
            else:
                count += 1

        if count:
            mop.reArrangeAssets()

        if len(errorL):
            cmds.confirmDialog(title='Error',
                               message="Could not import:\n{0}".format("\n".join(errorL)),
                               button=['OK'],
                               defaultButton='OK',
                               cancelButton='OK',
                               dismissString='OK',
                               icon="warning")

        return True if count else False

    def updateShotgun(self, addOnly=True):

        sgEntity = self.context["entity"]
        if sgEntity["type"].lower() != "shot":
            raise NotImplementedError("Only applies to shots.")

        #sShotCode = sgEntity["code"]
        sMsg = "You're about to update related assets in Shotgun.\n\nUpdate DB from Scene ?"
        sRes = pc.confirmDialog(title='ARE YOU SURE ?',
                                message=sMsg,
                                button=['OK', 'Cancel'],
                                defaultButton='Cancel',
                                cancelButton='Cancel',
                                dismissString='Cancel',
                                icon="warning")
        if sRes == "Cancel":
            pc.displayInfo("Canceled !")
            return

        proj = self.context['damProject']

        assetDataList = self.listAssetData()
        assetDataDct = OrderedDict((astData['name'], astData)
                                        for astData in assetDataList
                                            if astData["resource"] != noneValue)
        sAstNameList = assetDataDct.keys()

        sgProj = {"type":"Project", "id":proj._shotgundb._getProjectId()}
        filters = [["project", "is", sgProj],
                   ["code", "in", sAstNameList],
                   ]

        sg = proj._shotgundb.sg

        sgAssetList = sg.find("Asset", filters, ["code"])
#        sAstCodeList = tuple(sgAst["code"] for sgAst in sgAssetList)
#        sAstNotInSgList = tuple(s for s in sAstNameList if s not in sAstCodeList)

        proj.updateSgEntity(sgEntity, assets=sgAssetList)

        filters = [["shot", "is", sgEntity],
                   ]
        astShotConnList = sg.find("AssetShotConnection", filters, ["sg_occurences", "asset"])
        for astShotConn in astShotConnList:
            sAstName = astShotConn["asset"]["name"]
            iOccur = assetDataDct[sAstName]["occurences"]
            proj.updateSgEntity(astShotConn, sg_occurences=iOccur)

    def getCurrentTaskRefTag(self):

        sRefTag = ""

        sTaskName = self.context['task']['content']
        if sTaskName in REF_FOR_TASK:
            sRefTag = REF_FOR_TASK[sTaskName]
        else:
            raise EnvironmentError("No resource file associated with task: '{}'"
                                   .format(sTaskName))
        return sRefTag

    def do(self, s_inCmd):
        mop.do(s_inCmd, self.context['task']['content'], self)

    def getDuration(self):
        shot = self.context['entity']
        inOutDuration = shot['sg_cut_out'] - shot['sg_cut_in'] + 1
        duration = shot['sg_cut_duration']

        if inOutDuration != duration:
            pc.displayInfo("sg_cut_out - sg_cut_in = {} but sg_cut_duration = {}"
                           .format(inOutDuration, duration))

        if duration < 1:
            raise ValueError("Invalid shot duration: {}".format(duration))

        return duration

    def getShotCamNamespace(self):
        return 'cam_{0}'.format(self.context['entity']['code'])

    def getShotCamera(self):
        sCamName = self.getShotCamNamespace() + ":cam_shot_default"
        sCamList = cmds.ls(sCamName)
        if not sCamList:
            return None

        if len(sCamList) == 1:
            return pc.PyNode(sCamList[0])
        else:
            raise RuntimeError("Multiple cameras named '{}'".format(sCamName))

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

    pc.headsUpDisplay('HUD_ZOMBUser', section=0, block=pc.headsUpDisplay(nextFreeBlock=0), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=userInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBScene', section=2, block=pc.headsUpDisplay(nextFreeBlock=2), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=sceneInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBStep', section=4, block=pc.headsUpDisplay(nextFreeBlock=4), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=stepInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBFrame', section=5, block=pc.headsUpDisplay(nextFreeBlock=5), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=frameInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBFocal', section=7, block=pc.headsUpDisplay(nextFreeBlock=7), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=focalInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBEndFrame', section=9, block=pc.headsUpDisplay(nextFreeBlock=9), blockSize='small', label='', labelFontSize='small', dataFontSize='small', command=endFrameInfo, attachToRefresh=True)

    return headUpsValues

def restoreHUD(oldValues=None):
    pc.headsUpDisplay('HUD_ZOMBUser', rem=True)
    pc.headsUpDisplay('HUD_ZOMBScene', rem=True)
    pc.headsUpDisplay('HUD_ZOMBStep', rem=True)
    pc.headsUpDisplay('HUD_ZOMBFrame', rem=True)
    pc.headsUpDisplay('HUD_ZOMBFocal', rem=True)
    pc.headsUpDisplay('HUD_ZOMBEndFrame', rem=True)

    headsUps = pc.headsUpDisplay(listHeadsUpDisplays=True)

    if oldValues != None:
        for k, v in oldValues.iteritems():
            if k in headsUps:
                pc.headsUpDisplay(k, edit=True, visible=v)


def deleteHUD(*args, **kwargs):
    # FUNCTION QUI SEMBLE MANQUER, a ajouter quelque part apres le playblast
    # actuellement il y a un bug qui fait que t'as des script qui tournent en permanence dans la scene, et qui plante si
    # ce n'est pas une scene zombie avec une belle camera
    headsUps = cmds.headsUpDisplay(listHeadsUpDisplays=True)
    for i in headsUps:
        if "HUD_ZOMB" in i:
            print i
            cmds.headsUpDisplay(i, rem=True)


