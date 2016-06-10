#------------------------------------------------------------------
#               UI data and logic for sceneManagerUI.py
#------------------------------------------------------------------

import os
import re
import stat
from collections import OrderedDict
import shutil
from itertools import izip

import pymel.core as pc
import maya.cmds as mc
import maya.mel

#import tkMayaCore as tkc
from pytd.util.fsutils import pathResolve, normCase, pathSuffixed
from pytd.util.logutils import logMsg
from pytd.util.sysutils import toStr
from pytd.util.strutils import padded
from pytaya.core.general import copyAttrs, getObject
from pytaya.core import system as myasys

from davos.core import damproject
from davos.core.damtypes import DamShot, DamAsset
from davos_maya.tool.publishing import publishCurrentScene

from zomblib import shotgunengine
from zomblib.editing import playMovie
from zomblib import damutils

import dminutes.maya_scene_operations as mop
import dminutes.jipeLib_Z2K as jpZ
import dminutes.camImpExp as camIE
import dminutes.infoSetExp as infoE
from dminutes.geocaching import exportLayoutInfo, removeCacheReferences
#from dminutes.miscUtils import deleteUnknownNodes

reload(jpZ)
reload(camIE)
reload(infoE)

osp = os.path

# get zomb project
PROJECTNAME = os.environ.get("DAVOS_INIT_PROJECT")

okValue = 'OK'
noneValue = 'MISSING'
notFoundvalue = 'NOT FOUND'

#FROM DAVOS !!!!
RC_FOR_STEP = {'Previz 3D':'previz_scene',
               'Stereo':'stereo_scene',
               'Layout':'layout_scene',
               'Animation':'anim_scene',
               'Final Layout':'finalLayout_scene',
               }
RC_FOR_TASK = {}#{'previz 3D':'previz_scene', 'layout':'layout_scene'}

REF_FOR_STEP = {'Previz 3D':'previz_ref',
                'Layout':'anim_ref',
                'Animation':'anim_ref',
                'Final Layout':'render_ref',
                }
REF_FOR_TASK = {}

MOV_FOR_STEP = {'Previz 3D':('previz_capture',),
                'Stereo':('right_capture', 'left_capture',),
                'Layout':('layout_capture',),
                'Animation':('anim_capture',),
               }
MOV_FOR_TASK = {}


LIBS = {'Asset':'asset_lib', 'Shot':'shot_lib'}

MAX_INCR = 50

def rcFromTask(sgTask, fail=False):

    sTask = sgTask['content']
    sStep = sgTask['step']['name']

    sName = RC_FOR_TASK.get(sTask, RC_FOR_STEP.get(sStep, ""))

    if (not sName):
        sMsg = ("No resource file associated with task: {}".format(sgTask))
        if fail:
            raise EnvironmentError(sMsg)
        else:
            pc.displayError(sMsg)

    return sName

def refFromTask(sgTask, fail=False):

    sTask = sgTask['content']
    sStep = sgTask['step']['name']

    sName = REF_FOR_TASK.get(sTask, REF_FOR_STEP.get(sStep, ""))

    if (not sName):
        sMsg = ("No reference file associated with task: {}".format(sgTask))
        if fail:
            raise EnvironmentError(sMsg)
        else:
            pc.displayError(sMsg)

    return sName

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

        sSelList = mc.ls(sl=True)
        try:
            ret = func(*args, **kwargs)
        finally:
            if sSelList:
                try:
                    mc.select(sSelList)
                except Exception as e:
                    print "Could restore previous selection: {}".format(e)

        return ret
    return doIt

def iterIncrementFiles(sFilePath):

    for i in xrange(1, MAX_INCR + 1):
        p = pathSuffixed(sFilePath, "." + padded(i, 2))
        try:
            st = os.stat(p)
        except OSError:
            continue

        if stat.S_ISREG(st.st_mode):
            yield dict(path=p, mtime=st.st_mtime, num=i)

@restoreSelection
def makeCapture(sFilePath, start, end, width, height, displaymode="",
                showFrameNumbers=True, format="iff", compression="jpg",
                ornaments=False, play=False, useCamera=None, audioNode=None,
                camSettings=None, quick=False):
#                i_inFilmFit=0, i_inDisplayResolution=0, i_inDisplayFilmGate=0,
#                i_inOverscan=1.0, i_inSafeAction=0, i_inSafeTitle=0,
#                i_inGateMask=0, f_inMaskOpacity=0.8, quick=False):

    pc.select(cl=True)
    names = []
    name = ""

    pan = pc.playblast(activeEditor=True)
    #sViewType = mc.modelEditor(pan, q=True, viewType=True)
    #if sViewType == "stereoCameraView":

    #Camera settings
    oldCamera = None
    if useCamera:
        curCam = pc.modelEditor(pan, query=True, camera=True)
        if curCam != useCamera:
            oldCamera = curCam
            pc.modelEditor(pan, edit=True, camera=useCamera)

    app = pc.modelEditor(pan, query=True, displayAppearance=True)
    tex = pc.modelEditor(pan, query=True, displayTextures=True)
    wireOnShaded = pc.modelEditor(pan, query=True, wireframeOnShaded=True)
    xray = pc.modelEditor(pan, query=True, xray=True)
    jointXray = pc.modelEditor(pan, query=True, jointXray=True)
    hud = pc.modelEditor(pan, query=True, hud=True)

    oCamShape = pc.modelEditor(pan, query=True, camera=True)
    if oCamShape.type() == "transform":
        sCamShape = oCamShape.getShape().name()
    else:
        sCamShape = oCamShape.name()

    #visible types
    nurbsCurvesShowing = pc.modelEditor(pan, query=True, nurbsCurves=True)

    editorKwargs = dict(hud=ornaments, wireframeOnShaded=False, displayAppearance="smoothShaded")
    pc.modelEditor(pan, edit=True, nurbsCurves=False, **editorKwargs)

    playblastKwargs = dict(format=format, compression=compression, quality=90,
                           sequenceTime=False, clearCache=True, viewer=play,
                           showOrnaments=ornaments,
                           framePadding=4,
                           forceOverwrite=True,
                           percent=100,
                           startTime=start, endTime=end,
                           widthHeight=[width, height],
                           offScreen=True, #fixes clamping of the capture in Legacy viewports
                           )

    sAudioNode = audioNode
    if not sAudioNode:
        gPlayBackSlider = maya.mel.eval('$tmpVar=$gPlayBackSlider')
        sAudioNode = mc.timeControl(gPlayBackSlider, q=True, sound=True)

    if sAudioNode:
        sSoundPath = pathResolve(mc.getAttr(".".join((sAudioNode, "filename"))))
        if not os.path.exists(sSoundPath):
            pc.displayError("File of '{}' node not found: '{}' !"
                              .format(sAudioNode, sSoundPath))
        else:
            playblastKwargs.update(sound=sAudioNode)

    savedSettings = {}
    if camSettings:
        for sAttr, value in camSettings.iteritems():
            sNodeAttr = sCamShape + "." + sAttr
            savedSettings[sAttr] = mc.getAttr(sNodeAttr)
            pc.setAttr(sNodeAttr, value)

    try:
        if format == "iff" and showFrameNumbers:
            name = mc.playblast(filename=sFilePath, **playblastKwargs)

            for i in range(start, end + 1):
                oldFileName = name.replace("####", str(i).zfill(4))
                newFileName = oldFileName.replace(".", "_", 1)
                if os.path.isfile(newFileName):
                    os.remove(newFileName)
                os.rename(oldFileName, newFileName)
                names.append(newFileName)
        else:
            if format == "iff":
                name = mc.playblast(completeFilename=sFilePath, **playblastKwargs)
            else:
                name = mc.playblast(filename=sFilePath, **playblastKwargs)

            names.append(name)

    finally:
        #Reset values
        pc.modelEditor(pan, edit=True, displayAppearance=app,
                       displayTextures=tex,
                       wireframeOnShaded=wireOnShaded,
                       xray=xray,
                       jointXray=jointXray,
                       nurbsCurves=nurbsCurvesShowing,
                       hud=hud)
        #Camera
        if savedSettings:
            for sAttr, value in savedSettings.iteritems():
                pc.setAttr(sCamShape + "." + sAttr, value)

    if oldCamera:
        pc.modelEditor(pan, edit=True, camera=oldCamera)

    return names

class SceneManager():
    """Main Class to handle SceneManager Data and operations"""
    def __init__(self, d_inContext=None):
        self.context = {}
        self.projectname = "zombillenium"
        self.context['damProject'] = damproject.DamProject(self.projectname)

        if not self.context['damProject']:
            raise RuntimeError("Cannot initialize project '{0}'".format(self.projectname))

        mop.setMayaProject(self.projectname)

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
        proj = self.context['damProject']
        userOrNone = proj._shotgundb.currentUser if b_inMyTasks else None
        return proj._shotgundb.getTasks(self.context['entity'],
                                        self.context['step'], userOrNone)

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
        except Exception as e:
            pc.warning('damProject.getPath failed with {0}, {1}, {2} : {3}'.format(lib, s_inFileTag, tokens, e))

        return path

    def infosFromCurrentScene(self):
        """Retrieve the scene path and get davos data from it"""

        infos = {}

        proj = self.context['damProject']

        sCurScnPath = pc.sceneName()
        if sCurScnPath:
            sCurScnPath = os.path.abspath(sCurScnPath)
            privFile = proj.entryFromPath(sCurScnPath)
            if privFile:
                infos["priv_file"] = privFile
                infos["pub_file"] = privFile.getPublicFile()

                pathData = proj.dataFromPath(privFile)
                infos["path_data"] = pathData
                infos["dam_entity"] = proj._entityFromPathData(pathData, fail=False)

        return infos

    def contextFromSceneInfos(self, sceneInfos):
        """format davos data to match with UI Data to allow detection of current loaded scene"""

        davosContext = {}
        #proj = self.context['damProject']
        scnPathData = sceneInfos.get("path_data", {})
        #print "-------------", scnPathData
        if (("resource" not in scnPathData) or ("section" not in scnPathData)
            or ("name" not in scnPathData)):
            return None

        sSection = scnPathData["section"]
        if sSection == "shot_lib":

            sSgStep = scnPathData.get("sg_step")
            if not sSgStep:
                return None

            davosContext['step'] = sSgStep
            davosContext['seq'] = scnPathData["sequence"]
            davosContext['shot'] = scnPathData["name"]

        elif sSection == "asset_lib":
            pc.warning("asset_lib section not managed yet !!")
            return None
        else:
            pc.warning("Unknown section {0}".format(scnPathData["section"]))
            return None

        return davosContext

    def assertEntitiesMatchUp(self, sceneInfos):

        ctxEntity = self.getDamEntity()
        scnEntity = sceneInfos.get("dam_entity")
        if not scnEntity:
            raise AssertionError("Current scene is neither an Asset nor a Shot.")

        if scnEntity.sgEntityType != ctxEntity.sgEntityType:
            raise AssertionError("Entity types differ: Current scene is a {} but Scene Manager displays a {}."
                                 .format(scnEntity.sgEntityType, ctxEntity.sgEntityType))

        if scnEntity.name != ctxEntity.name:
            raise AssertionError("Entity names differ: Current scene is '{}' but Scene Manager displays '{}'."
                                 .format(scnEntity.name, ctxEntity.name))

        return True

    def entitiesMatchUp(self, sceneInfos):
        try:
            self.assertEntitiesMatchUp(sceneInfos)
        except AssertionError as e:
            logMsg(toStr(e), log="debug")
            return False
        return True

    def assertResourcesMatchUp(self, sceneInfos):
        """Compare davos data with UI data, return True if they match"""

        self.assertEntitiesMatchUp(sceneInfos)

        ctxRcFile = self.rcFileFromContext()
        if not ctxRcFile:
            raise AssertionError("Could not get davos resource from current context.")

        scnRcFile = sceneInfos.get("pub_file")
        if not scnRcFile:
            raise AssertionError("Could not get davos resource from current scene.")

        if scnRcFile != ctxRcFile:
            sMsgLines = ("Resource files differ:",
                         "Current Scene: '{}'".format(scnRcFile.absPath()),
                         "Scene Manager: '{}'".format(ctxRcFile.absPath())
                        )
            raise AssertionError("\n    - ".join(sMsgLines))

        return True

    def resourcesMatchUp(self, sceneInfos):
        try:
            self.assertResourcesMatchUp(sceneInfos)
        except AssertionError as e:
            logMsg(toStr(e), log="debug")
            return False
        return True

    def assertScenePublishable(self, sceneInfos=None):

        if sceneInfos is None:
            sceneInfos = self.infosFromCurrentScene()
            self.assertResourcesMatchUp(sceneInfos)

        scnPubFile = sceneInfos["pub_file"]
        scnPubFile.assertEditedVersion(sceneInfos["priv_file"], outcomes=False,
                                       remember=False)
        try:
            scnPubFile.ensureLocked(autoLock=False)
        except RuntimeError as e:
            raise AssertionError(e.message)

        return True

    def scenePublishable(self, sceneInfos):
        try:
            self.assertScenePublishable(sceneInfos)
        except AssertionError as e:
            logMsg(toStr(e), log="debug")
            return False
        return True

    def refreshSceneContext(self):
        """Retrieve the scene path and get davos data from it"""
        self.context['sceneEntry'] = None
        self.context['sceneData'] = {}
        proj = self.context['damProject']

        curScenePath = pc.sceneName()
        if curScenePath:
            curScenePath = os.path.abspath(curScenePath)
            entry = proj.entryFromPath(curScenePath)
            if entry is not None:
                self.context['sceneEntry'] = entry
                self.context['sceneData'] = proj.dataFromPath(curScenePath)

        return self.contextIsMatching()

    def contextIsMatching(self):
        """Compare davos data with UI data, return True if they match"""
        self.context['sceneState'] = ""
        contextEntry = self.getEntry()

        if contextEntry is None or self.context['sceneEntry'] is None:
            self.context['sceneState'] = "Cannot autodetect context !"
            return False

        sceneEntryPath = self.context['sceneEntry'].getPublicFile().absPath()
        if contextEntry.absPath() == sceneEntryPath:
            iSrcVers = self.context['sceneEntry'].versionFromName()
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

        if not entry:
            entry = self.rcFileFromContext()
        else:
            self.context['lock'] = entry.getLockOwner()

    def getDamEntity(self):

        sgEntity = self.context['entity']
        sEntityType = sgEntity['type']
        sEntityName = sgEntity['code']

        proj = self.context['damProject']

        if sEntityType == 'Shot':
            damEntity = proj.getShot(sEntityName)
        elif sEntityType == 'Asset':
            damEntity = proj.getAsset(sEntityName)
        else:
            raise TypeError("Unexpected entity type: '{}'".format(sEntityType))

        return damEntity

    def rcFileFromContext(self, weak=False, fail=False):
        """Get davos entry from UI data"""

        entry = None

        if 'task' not in self.context:
            if fail:
                raise RuntimeError("Current context has no task defined.")
            return None

        sRcName = rcFromTask(self.context['task'])
        if sRcName:
            try:
                damEntity = self.getDamEntity()
                entry = damEntity.getRcFile("public", sRcName, weak=weak, fail=fail)
            except Exception as e:
                if fail:
                    raise
                pc.warning(toStr(e))

        return entry

    def createFolder(self):
        nameKey = 'name'

        if self.context['entity']['type'] == 'Shot':
            nameKey = 'code'

            damShot = DamShot(self.context['damProject'], name=self.context['entity'][nameKey])
            damShot.createDirsAndFiles()

    def save(self, force=True):
        entry = self.rcFileFromContext()

        if not entry:
            pc.error("Cannot get entry for context {0}".format(self.context))

        currentScene = os.path.abspath(pc.sceneName())
        if not currentScene:
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

        if not mc.file(q=True, modified=True):
            return currentScene

        return pc.saveAs(currentScene, force=force)#, postSaveScript="""python("print 100*'#'")""")

    def saveIncrement(self, force=True):
        # new incrementing system based on the last versoin present in the folder
        entry = self.rcFileFromContext()

        if entry == None:
            pc.error("Cannot get entry for context {0}".format(self.context))

        currentScene = os.path.abspath(pc.sceneName())
        if currentScene == '':
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

        matches = re.match(".*(v\d{3})\.(\d{3})\.ma", currentScene)

        if matches:
            print "currentScene=", currentScene
            newFileName = jpZ.createIncrementedFilePath(filePath=currentScene, vSep=".", extSep=".ma", digits=3,)

            if (not force) and os.path.isfile(newFileName):
                pc.error("File already exists ({0})!".format(newFileName))
            else:
                return pc.saveAs(newFileName, force=force)

            pc.warning("Invalid file pattern !")

        return None

    def playLatestCapture(self, sendToRv):

        context = self.context
        proj = context['damProject']
        sStep = context['step']['code']
        sTask = context['task']['content']
        damShot = self.getDamShot()
        sWipCaptDirPath = mop.getWipCaptureDir(damShot)
        seqId = context["entity"]["sg_sequence"]["id"]

        sScenePath = pc.sceneName()
        sceneFile = proj.entryFromPath(sScenePath, space="private")
        v, w = sceneFile.getEditNums()

        sCaptRcName = MOV_FOR_TASK.get(sTask, MOV_FOR_STEP.get(sStep, [None]))[-1]
        if not sCaptRcName:
            pc.displayWarning("No capture defined for '{}|{}'".format(sStep, sTask))
            return

        pubCaptFile = damShot.getRcFile("public", sCaptRcName, weak=True, dbNode=False)
        privCaptFile = pubCaptFile.getEditFile(v, w, weak=True)

        sLatestPath = privCaptFile.absPath() if privCaptFile.isFile() else ""

        sWipCaptPath = osp.join(sWipCaptDirPath, privCaptFile.name)
        incrementFiles = sorted(iterIncrementFiles(sWipCaptPath), key=lambda d:d["mtime"])
        if incrementFiles:
            wipFile = incrementFiles[-1]
            if not sLatestPath:
                sLatestPath = wipFile["path"]
            elif wipFile["mtime"] > osp.getmtime(sLatestPath):
                sLatestPath = wipFile["path"]

        if not sLatestPath:
            pc.displayError("No capture has been made yet.")
            return

        playKwargs = dict()
        if sendToRv:
            playKwargs.update(pushToRv="playblast", sequenceId=seqId)

        return playMovie(sLatestPath, **playKwargs)

    @mop.undoAtOnce
    def capture(self, saveScene=False, increment=False, quick=True, sendToRv=False, smoothData=None):
        # BUG pas de son alors que son present dans la scene
        # BUG first frame decalee dupliquee dans les fichier output
        global CAPTURE_INFOS

        sSavedFile = None

        context = self.context
        proj = context['damProject']
        sStep = context['step']['code']
        sTask = context['task']['content']
        damShot = self.getDamShot()

        sCaptRcList = MOV_FOR_TASK.get(sTask, MOV_FOR_STEP.get(sStep))
        if not sCaptRcList:
            pc.displayWarning("No capture defined for '{}|{}'".format(sStep, sTask))
            return

        oShotCam = self.getShotCamera(fail=True)

        sWipCaptDirPath = mop.getWipCaptureDir(damShot)
        seqId = context["entity"]["sg_sequence"]["id"]

        CAPTURE_INFOS['cam'] = oShotCam.getShape().name()
        oCamRef = oShotCam.referenceFile()
        if oCamRef:
            bWasLocked = oCamRef.refNode.getAttr("locked")
            oShotCam = mop.setCamRefLocked(oShotCam, False)
            oCamRef.importContents()
            mop.setShotCamLocked(oShotCam, bWasLocked)
            oCamRef = None

        pubCaptureFiles = []
        for sCaptRcName in sCaptRcList:
            pubCaptFile = damShot.getRcFile("public", sCaptRcName, weak=True, dbNode=False)
            pubCaptureFiles.append((sCaptRcName, pubCaptFile))

        oStereoCam = None
        if sStep.lower() == "stereo":
            oStereoCam = self.getStereoCam(fail=True)

        if sStep.lower() == sTask.lower():
            CAPTURE_INFOS['task'] = sTask
        else:
            CAPTURE_INFOS['task'] = sStep + " | " + sTask

        CAPTURE_INFOS['user'] = proj._shotgundb.currentUser['name']

        sCamFile = ""
        if (not quick) and sStep.lower() != "previz 3d":

            abcFile = damShot.getRcFile("public", "camera_abc", weak=True)

            bShotCamEdited = self.isShotCamEdited()

            oCamAbcNode = self.getShotCamAbcNode()
            if oCamAbcNode:
                sAbcNodePath = pathResolve(oCamAbcNode.getAttr("abc_File"))
                if osp.normcase(sAbcNodePath) != osp.normcase(abcFile.absPath()):
                    raise RuntimeError("Unexpected path on '{}' node: \n         got: '{}'\n    expected: '{}'")

            if abcFile.exists():
                if bShotCamEdited:
                    sCamFile = abcFile.nextVersionName()
                else:
                    latestAbcFile = abcFile.latestVersionFile()
                    if latestAbcFile:
                        sCamFile = latestAbcFile.name

        CAPTURE_INFOS['cam_file'] = sCamFile

        if not quick:
            #Get start/end from shotgun
            captureStart = 101
            duration = self.getDuration()
            captureEnd = captureStart + duration - 1
        else:
            captureStart = pc.playbackOptions(q=True, minTime=True)
            captureEnd = pc.playbackOptions(q=True, maxTime=True)

        CAPTURE_INFOS['start'] = captureStart
        CAPTURE_INFOS['end'] = captureEnd

        if saveScene:
            if increment:
                sSavedFile = self.saveIncrement(force=False)
            else:
                sSavedFile = self.save(force=False)

            if not sSavedFile:
                raise RuntimeError("Could not save current scene !")

        #Infer captures path
        sScenePath = pc.sceneName()
        CAPTURE_INFOS['scene'] = os.path.basename(sScenePath)

        sceneFile = proj.entryFromPath(sScenePath, space="private")
        v, w = sceneFile.getEditNums()

        outCapturePaths = []
        for sCaptRcName, pubCaptFile in pubCaptureFiles:
            privCaptFile = pubCaptFile.getEditFile(v, w, weak=True)
            if quick:
                sWipCaptPath = osp.join(sWipCaptDirPath, privCaptFile.name)

                incrementFiles = sorted(iterIncrementFiles(sWipCaptPath),
                                        key=lambda d:d["mtime"])
                if incrementFiles:
                    incrFile = incrementFiles[-1]
                    j = (incrFile["num"] % MAX_INCR) + 1
                    sCapturePath = pathSuffixed(sWipCaptPath, "." + padded(j, 2))
                else:
                    sCapturePath = pathSuffixed(sWipCaptPath, "." + padded(1, 2))
            else:
                sCapturePath = privCaptFile.absPath()

            outCapturePaths.append((sCaptRcName, sCapturePath))

        bImgPlnViz = mop.isImgPlaneHidden()
        mop.setImgPlaneHidden(True)

        numSmoothed = 0
        sRecorder = ""
        try:
            oShotCam.setAttr('aspectRatio', 1.85)

            if smoothData:
                sMeshList = sorted(smoothData.iterkeys())
                for sMesh in sMeshList:
                    mc.setAttr(sMesh + ".displaySmoothMesh", 2)
                    numSmoothed += 1

            camSettings = dict(filmFit=1, displayResolution=0, displayFilmGate=1,
                               displaySafeAction=1, overscan=1.0,
                               displaySafeTitle=0, displayGateMask=1,
                               displayGateMaskOpacity=1.0)

            bArrangeViews = True
            if oStereoCam:
                if (not quick):
                    sRecorder = mop.getStereoInfosRecorder(oStereoCam.name())
                camSettings = None
            else:
                sPanelList = tuple(mop.iterPanelsFromCam(oShotCam, visible=True))
                if sPanelList:
                    sBlastPanel = sPanelList[0]
                    sEditor = mc.modelPanel(sBlastPanel, q=True, modelEditor=True)
                    mc.modelEditor(sEditor, e=True, activeView=True)
                    bArrangeViews = False

            if bArrangeViews:
                if not mc.panelConfiguration("savedBeforeCapture", ex=True):
                    sPanelConf = mc.panelConfiguration("savedBeforeCapture", sceneConfig=True)
                    mc.panelConfiguration(sPanelConf, e=True, label="Saved Before Capture")

                pc.mel.updatePanelLayoutFromCurrent("Saved Before Capture")

                _, oImgPlaneCam = mop.getImagePlaneItems(create=False)
                mop.arrangeViews(oShotCam, oImgPlaneCam, oStereoCam, singleView=True)

            width, height = (1280, 720)
            bAoEnabled = mc.getAttr('hardwareRenderingGlobals.ssaoEnable')
            if (not quick) and sStep.lower() == "animation":
                width, height = (1920, 1080)
                mc.setAttr('hardwareRenderingGlobals.ssaoEnable', True)

            iFontMode = mc.displayPref(q=True, fontSettingMode=True)
            iFontSize = mc.displayPref(q=True, smallFontSize=True)
            mc.displayPref(fontSettingMode=2)
            mc.displayPref(smallFontSize=12)
            savedHudValues = createHUD()

            for sCaptRcName, sCapturePath in outCapturePaths:

                if oStereoCam:
                    sStereoMode = sCaptRcName.split("_", 1)[0] + "Eye"
                    mc.stereoCameraView("StereoPanelEditor", e=True, displayMode=sStereoMode)
                    mc.refresh()

                res = makeCapture(sCapturePath, captureStart, captureEnd, width, height,
                                  format="qt", compression="H.264", camSettings=camSettings,
                                  ornaments=True, play=False, quick=quick)

                sOutFilePath = res[0]
                if not quick:
                    try:
                        shutil.copystat(sScenePath, sOutFilePath)
                    except Exception as e:
                        pc.displayWarning(toStr(e))
        finally:
            try:
                restoreHUD(savedHudValues)
                mc.displayPref(smallFontSize=iFontSize)
                mc.displayPref(fontSettingMode=iFontMode)
                mc.setAttr('hardwareRenderingGlobals.ssaoEnable', bAoEnabled)
            except Exception as e:
                pc.displayError(toStr(e))

            if sRecorder:
                mc.delete(sRecorder)

            oShotCam.setAttr('aspectRatio', 1.7778)

            if numSmoothed:
                for i in xrange(numSmoothed):
                    sMesh = sMeshList[i]
                    meshInfo = smoothData[sMesh]
                    for k, v in meshInfo.iteritems():
                        if k.startswith("."):
                            mc.setAttr(sMesh + k, v)

            mop.setImgPlaneHidden(bImgPlnViz)

            if bArrangeViews:
                pc.mel.setNamedPanelLayout("Saved Before Capture")
                sPanelConf = mc.getPanel(configWithLabel="Saved Before Capture")
                if sPanelConf:
                    mc.deleteUI(sPanelConf, panelConfig=True)

                if oStereoCam:
                    mc.stereoCameraView("StereoPanelEditor", e=True, displayMode="interlace")

        if sRecorder:
            sPrivInfoPath = damShot.getPath("private", "stereoCam_info")
            try:
                mop.writeStereoInfos(sPrivInfoPath)
            except Exception as e:
                pc.displayError("Could not write stereo infos: " + toStr(e))

        playKwargs = dict()
        if sendToRv:
            playKwargs.update(pushToRv="playblast", sequenceId=seqId)

        return playMovie(sOutFilePath, **playKwargs)

    def edit(self, editInPlace=None, onBase=False):
        privFile = None

        damEntity = self.getDamEntity()
        proj = damEntity.project

        if 'task' not in self.context:
            pc.displayError('Task missing from current context !')
            return

        sgTask = self.context['task']
        sRcName = rcFromTask(sgTask)
        if not sRcName:
            return

        path = None
        try:
            path = damEntity.getPath('public', sRcName)
        except Exception, e:
            pc.warning('damProject.getPath failed : {0}'.format(e))

        if not path:
            return

        entry = proj.entryFromPath(path)
        if not entry:
            sMsg = "No such file: '{}'".format(path)
            pc.confirmDialog(title='SORRY !',
                             message=sMsg,
                             button=["OK"],
                             icon="critical",
                            )
            raise EnvironmentError(sMsg)

        result = "Yes" if editInPlace else "No"

        if editInPlace is None:
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
            mc.file(rename=newpath)
            mc.file(save=True)
        else:
            privFile = entry.edit(openFile=not onBase, existing='choose')#existing values = choose, fail, keep, abort, overwrite

        if privFile is None:
            pc.warning('There was a problem with the edit !')
        else:
            pass
            #print "privFile " + str(privFile.absPath())

        return privFile

    def prePublishCurrentScene(self, publishCtx, **kwargs):

        sStepCode = self.context["step"]["code"].lower()

        if sStepCode == "final layout":
            removeCacheReferences()

        if sStepCode not in ("previz 3d", "stereo") and self.isShotCamEdited():
            self.exportCamAnimFiles(publish=True)
            self.importShotCamAbcFile()
            mop.setCamAsPerspView(self.getShotCamera())

    def postPublishCurrentScene(self, publishCtx, **kwargs):

        pubFile = publishCtx.sceneInfos["public_file"]
        v = publishCtx.prePublishInfos["version"]
        sComment = "from {}".format(pubFile.nameFromVersion(v))

        sStepCode = self.context["step"]["code"].lower()

        if sStepCode == "stereo":
            self.exportStereoCamFiles(publish=True, comment=sComment)
            return

        # here is incerted the publish of the camera of the scene
        print "exporting the camera of the shot"
        camImpExpI = camIE.camImpExp()
        camImpExpI.exportCam(sceneName=jpZ.getShotName())

        if sStepCode in ("previz 3d", "layout"):
            # here is the publish of the infoSet file with the position of the global and local srt of sets assets
            infoSetExpI = infoE.infoSetExp()
            infoSetExpI.export(sceneName=jpZ.getShotName())

        if sStepCode == "layout":
            exportLayoutInfo(publish=True, comment=sComment)

    def assertBeforePublish(self):

        #proj = self.context['damProject']

        currentScene = os.path.abspath(pc.sceneName())
        if not currentScene:
            raise AssertionError("Please save your scene as a valid private working scene (Edit if needed)")

        #curScnFile = proj.entryFromPath(currentScene, fail=True)

        sFixMsg = "\n\nPlease, apply a 'Shot Setup' and retry."
        oShotCam = None
        try:
            oShotCam = self.getShotCamera(fail=True)
        except Exception as e:
            raise AssertionError(toStr(e) + sFixMsg)

        return oShotCam

    def publish(self):
        try:
            self.assertBeforePublish()
        except AssertionError as e:
            pc.confirmDialog(title='SORRY !',
                             message=toStr(e),
                             button=["OK"],
                             defaultButton="OK",
                             cancelButton="OK",
                             dismissString="OK",
                             icon="critical")
            return False

        res = publishCurrentScene(prePublishFunc=self.prePublishCurrentScene,
                                  postPublishFunc=self.postPublishCurrentScene)

        return res

    def getShotgunContent(self):
        #print 'getShotgunContent ' + self.context['entity']['code']
        content = self.context['damProject']._shotgundb.getShotAssets(self.context['entity']['code'])
        return content if content is not None else []

    def getFileTagFromPath(self, in_sPath):
        """Detect the filetag (resource) from an asset path, when we don't have the shotgun info, right now it'll just say 'NONE'"""
        return notFoundvalue

    def listRelatedAssets(self):
        """Compare Shotgun shot<=>assets linking and scene content"""
        logMsg(log='all')

        astShotConnList = self.getShotgunContent()
        assetShotConnDct = dict((d['asset']['name'].lower(), d) for d in astShotConnList)

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

            pathData = proj.dataFromPath(sRefPath, library=astLib, warn=False)

            astData = initData.copy()
            astData.update(path=sRefPath, file_refs=oFileRefDct[sRefNormPath])

            if not pathData:
                assetDataList.append(astData)
                continue

            astData.update(pathData)

            sAstKey = astData["name"].lower()
            if sAstKey in assetShotConnDct:
                astData.update(sg_info=okValue, sg_asset_shot_conn=assetShotConnDct[sAstKey])
                sFoundAstList.append(sAstKey)

            assetDataList.append(astData)

        for sAstKey, astShotConn in assetShotConnDct.iteritems():
            if sAstKey not in sFoundAstList:
                astData = initData.copy()
                astData.update(name=astShotConn['asset']['name'], sg_info=okValue,
                               sg_asset_shot_conn=astShotConn)
                assetDataList.append(astData)

        allMyaFileDct = {}
        allMyaFileList = []
        for astData in assetDataList:

            sAstName = astData['name']
            if not sAstName:
                continue

            damAst = DamAsset(proj, name=sAstName)
            drcLib = damAst.getLibrary()

            entryFromPath = lambda p: proj.entryFromPath(p, library=drcLib, dbNode=False)
            mayaRcIter = damAst.iterMayaRcItems(filter="*_ref")
            mayaFileItems = tuple((n, entryFromPath(p)) for n, p in mayaRcIter)

            allMyaFileDct[sAstName] = mayaFileItems
            allMyaFileList.extend(f for _, f in mayaFileItems if f)

        dbNodeList = proj.dbNodesForResources(allMyaFileList)
        for mrcFile, dbNode in izip(allMyaFileList, dbNodeList):
            if not dbNode:
                mrcFile.getDbNode(fromCache=False)

        for astData in assetDataList:

            sAstName = astData['name']
            if not sAstName:
                continue

            mayaFileItems = allMyaFileDct[sAstName]

            astRcDct = {}
            for sRcName, mrcFile in mayaFileItems:

                rcDct = {"drc_file":mrcFile, "status":okValue}
                astRcDct[sRcName] = rcDct

                if not mrcFile:
                    sMsg = noneValue
                    rcDct["status"] = sMsg
                    continue

#                cachedDbNode = mrcFile.getDbNode(fromDb=False)
#                if cachedDbNode:
#                    mrcFile.refresh(simple=True)
#                else:
#                    mrcFile.getDbNode(fromCache=False)

                if not mrcFile.currentVersion:
                    sMsg = "NO VERSION"
                    rcDct["status"] = sMsg
                    continue

                try:
                    mrcFile.assertUpToDate(refresh=False)
                except AssertionError as e:
                    pc.displayWarning(e.message)
                    sMsg = "OUT OF SYNC"
                    rcDct["status"] = sMsg
                    continue

            astData["maya_refs"] = astRcDct
            astData["occurences"] = len(astData["file_refs"])

        return assetDataList

    def updateSceneAssets(self):
        """Updates scene Assets from shotgun shot<=>assets linking"""

        sgEntity = self.context["entity"]
        if sgEntity["type"].lower() != "shot":
            raise NotImplementedError("Only applies to shots.")

        # WIP CORRECTION collapseVariables (ERROR)
        assetDataList = self.listRelatedAssets()
        errorL = []
        sCurRefTag = refFromTask(self.context["task"], fail=True)

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
                errorTxt = "'{0}' : {1}".format(astData['name'], err)
                print errorTxt
                errorL.append(errorTxt)
            else:
                count += 1

        if count:
            mop.reArrangeAssets()

        if len(errorL):
            sSep = "\n- "
            mc.confirmDialog(title='WARNING !',
                               message="Could not load assets:\n{}".format(sSep + sSep.join(errorL)),
                               button=['OK'],
                               defaultButton='OK',
                               cancelButton='OK',
                               dismissString='OK',
                               icon="warning")

        return True if count else False

    def updateShotgunAssets(self):

        sgEntity = self.context["entity"]
        if sgEntity["type"].lower() != "shot":
            raise NotImplementedError("Only applies to shots.")

        #sShotCode = sgEntity["code"]
        sMsg = "You're about to update related assets in Shotgun.\n\nUpdate Assets In Shotgun ?"
        sRes = pc.confirmDialog(title='DO YOU WANT TO...',
                                message=sMsg,
                                button=['OK', 'Cancel'],
                                defaultButton='Cancel',
                                cancelButton='Cancel',
                                dismissString='Cancel',
                                icon="question")
        if sRes == "Cancel":
            pc.displayInfo("Canceled !")
            return False

        proj = self.context['damProject']
        sg = proj._shotgundb.sg
        sgProj = {"type":"Project", "id":proj._shotgundb._getProjectId()}

        assetDataList = self.listRelatedAssets()
        assetDataDct = OrderedDict((astData['name'], astData)
                                        for astData in assetDataList
                                            if astData["resource"] != noneValue)

        filters = [["project", "is", sgProj], ["code", "in", assetDataDct.keys()]]
        scnSgAstList = sg.find("Asset", filters, ["code", "parents", "sg_sous_type"])

        addSgAstList = (sgAst for sgAst in scnSgAstList
                        if assetDataDct[sgAst["code"]]["sg_info"] == noneValue)

        addSgAstDct = dict((d["parents"][0]["name"], d)
                                for d in addSgAstList if  d["parents"])

        remSgAstList = tuple(d["sg_asset_shot_conn"]["asset"] for d in assetDataList
                             if d["sg_info"] == okValue and d["resource"] == noneValue)

        sMsgList = []
        for remSgAst in remSgAstList:

            if remSgAst["sg_sous_type"] != "1-primaire":
                continue

            parents = remSgAst["parents"]
            if not parents:
                continue

            sParentName = parents[0]["name"]
            if sParentName in addSgAstDct:
                sMsg = "'{}' WITH '{}'".format(addSgAstDct[sParentName]["code"],
                                                 remSgAst["code"])
                sMsgList.append(sMsg)

        if sMsgList:
            sSep = "\n- "
            sMsg = "You are going to replace:\n".upper() + sSep
            sMsg += sSep.join(sMsgList)
            sRes = pc.confirmDialog(title='WARNING !!',
                                    message=sMsg,
                                    button=['OK', 'Cancel'],
                                    defaultButton='Cancel',
                                    cancelButton='Cancel',
                                    dismissString='Cancel',
                                    icon="warning")
            if sRes == "Cancel":
                pc.displayInfo("Canceled !")
                return False

        proj.updateSgEntity(sgEntity, assets=scnSgAstList)

        filters = [["shot", "is", sgEntity], ]
        astShotConnList = sg.find("AssetShotConnection", filters, ["sg_occurences", "asset"])
        for astShotConn in astShotConnList:
            sAstName = astShotConn["asset"]["name"]
            iOccur = assetDataDct[sAstName]["occurences"]
            proj.updateSgEntity(astShotConn, sg_occurences=iOccur)

        return True

    def do(self, s_inCmd):
        mop.do(s_inCmd, self.context['task']['content'], self)

    def getDuration(self):
        return damutils.getShotDuration(self.context['entity'])

    def setPlaybackTimes(self):
        duration = self.getDuration()
        times = damutils.playbackTimesFromDuration(duration)
        mc.playbackOptions(edit=True, **times)

    def mkShotCamNamespace(self):
        return mop.mkShotCamNamespace(self.context['entity']['code'].lower())

    def getShotCamera(self, fail=False):
        return mop.getShotCamera(self.context['entity']['code'].lower(), fail=fail)

    def getStereoCam(self, fail=False):
        return mop.getStereoCam(self.context['entity']['code'].lower(), fail=fail)

    def importShotCam(self):

        sCamNspace = self.mkShotCamNamespace()
        if mc.namespace(exists=sCamNspace):
            raise RuntimeError("Namespace already exists: '{}'".format(sCamNspace))

        damCam = self.context["damProject"].getAsset("cam_shot_default")
        camFile = damCam.getResource("public", "scene")
        camFile.mayaImportScene(ns=sCamNspace, reference=False)
        mc.refresh()

        try:
            mc.parent(sCamNspace + ":asset", "grp_camera")
        except Exception as e:
            pc.displayWarning(toStr(e))

        return pc.PyNode(sCamNspace + ":cam_shot_default")

    def getDamShot(self):
        sEntityType = self.context['entity']['type'].lower()
        if sEntityType != 'shot':
            raise TypeError("Unexpected entity type: '{}'".format(sEntityType))

        sShotCode = self.context['entity']['code'].lower()
        proj = self.context["damProject"]
#        shotLib = proj.getLibrary("public", "shot_lib")
        return DamShot(proj, name=sShotCode)

    def getShotCamAbcNode(self):

        sShotCamNs = self.mkShotCamNamespace()

        def iterFuture(sAbcNode):
            sFutureList = mc.listHistory(sAbcNode, future=True)
            if sFutureList is not None:
                sFutureList.remove(sAbcNode)
                for sNodePath in sFutureList:
                    sNodeName = sNodePath.rsplit("|", 1)[-1]
                    if sNodeName.startswith(sShotCamNs + ":"):
                        yield sNodePath

        sAbcNodeList = []
        for sAbcNode in mc.ls(type="AlembicNode"):
            sFuturList = tuple(iterFuture(sAbcNode))
            if sFuturList:
                sAbcNodeList.append(sAbcNode)

        if not sAbcNodeList:
            return None
        elif len(sAbcNodeList) > 1:
            raise RuntimeError("Multiple AlembicNode found: {}".format(sAbcNodeList))
        else:
            return pc.PyNode(sAbcNodeList[0])

    def camAnimFilesExist(self):

        damShot = self.getDamShot()

        sPubAtomPath = damShot.getPath("public", "camera_atom")
        sPubAbcPath = damShot.getPath("public", "camera_abc")

        return (osp.exists(sPubAtomPath) and osp.exists(sPubAbcPath))

    def exportCamAnimFiles(self, publish=False):

        damShot = self.getDamShot()

        oCamAstGrp = pc.PyNode(mop.mkShotCamNamespace(damShot.name) + ":asset")

        self.setPlaybackTimes()

        sPrivAtomPath = damShot.getPath("private", "camera_atom")
        sPrivAbcPath = damShot.getPath("private", "camera_abc")

        for p in (sPrivAtomPath, sPrivAbcPath):
            sDirPath = os.path.dirname(p)
            if not os.path.exists(sDirPath):
                os.makedirs(sDirPath)

        pc.select(oCamAstGrp)
        myasys.exportAtomFile(sPrivAtomPath,
                              SDK=False,
                              constraints=False,
                              animLayers=True,
                              statics=True,
                              baked=True,
                              points=False,
                              hierarchy="below",
                              channels="all_keyable",
                              timeRange="all",
                              )

        mop.exportCamAlembic(root=oCamAstGrp.longName(), file=sPrivAbcPath)

        if publish:

            pubShotLib = damShot.getLibrary("public")
            sComment = "from {}".format(pc.sceneName().basename())
            results = []

            sPubAtomPath = damShot.getPath("public", "camera_atom")
            sPubAbcPath = damShot.getPath("public", "camera_abc")

            sFilePathItems = ((sPrivAtomPath, sPubAtomPath), (sPrivAbcPath, sPubAbcPath))
            for sPrivPath, sPubPath in sFilePathItems:
                sDirPath = osp.dirname(sPubPath)
                parentDir = pubShotLib.getEntry(sDirPath, dbNode=False)
                res = parentDir.publishFile(sPrivPath, autoLock=True, autoUnlock=True,
                                            comment=sComment, dryRun=False)
                results.append(res)

            return results

    def exportStereoCamFiles(self, publish=False, comment=""):

        damShot = self.getDamShot()
        sShotCode = damShot.name

        oStereoCam = self.getStereoCam(fail=True).getShape()
        sStereoNs = mop.mkStereoCamNamespace(sShotCode)
        sStereoGrp = getObject(sStereoNs + ":grp_stereo", fail=True)
        sAtomFixCam = getObject(sStereoNs + ":atomFix_" + oStereoCam.nodeName(stripNamespace=True), fail=True)

        self.setPlaybackTimes()

        sPrivAtomPath = damShot.getPath("private", "stereoCam_anim")
        sPrivInfoPath = damShot.getPath("private", "stereoCam_info")
        if not osp.isfile(sPrivInfoPath):
            sPrivInfoPath = ""

        for p in (sPrivAtomPath, sPrivInfoPath):
            if not p: continue
            sDirPath = os.path.dirname(p)
            if not os.path.exists(sDirPath):
                os.makedirs(sDirPath)

        sAttrList = pc.listAttr(oStereoCam, k=True)
        sAttrList = copyAttrs(oStereoCam, sAtomFixCam, *sAttrList,
                              create=False, values=True, inConnections=True)

        pc.select(sStereoGrp)
        myasys.exportAtomFile(sPrivAtomPath,
                              SDK=False,
                              constraints=False,
                              animLayers=True,
                              statics=True,
                              baked=True,
                              points=False,
                              hierarchy="below",
                              channels="all_keyable",
                              timeRange="all",
                              )

        sAttrList = copyAttrs(sAtomFixCam, oStereoCam, *sAttrList,
                              create=False, values=True, inConnections=True)

        if publish:

            pubShotLib = damShot.getLibrary("public")
            if comment:
                sComment = comment
            else:
                sComment = "from {}".format(pc.sceneName().basename())
            results = []

            sPubAtomPath = damShot.getPath("public", "stereoCam_anim")
            sPubInfoPath = damShot.getPath("public", "stereoCam_info")

            sFilePathItems = ((sPrivAtomPath, sPubAtomPath), (sPrivInfoPath, sPubInfoPath))
            for sPrivPath, sPubPath in sFilePathItems:
                if not sPrivPath:
                    continue
                sDirPath = osp.dirname(sPubPath)
                parentDir = pubShotLib.getEntry(sDirPath, dbNode=False)
                res = parentDir.publishFile(sPrivPath, autoLock=True, autoUnlock=True,
                                            comment=sComment, dryRun=False)
                results.append(res)

            return results

    def importShotCamAbcFile(self):

        damShot = self.getDamShot()
        abcFile = damShot.getResource("public", "camera_abc", fail=True)

        oCamAstGrp = pc.PyNode(self.mkShotCamNamespace() + ":asset")
        sCamAstGrp = oCamAstGrp.longName()
        oFileRef = oCamAstGrp.referenceFile()
        oShotCam = self.getShotCamera()

        if oFileRef:
            mop.setReferenceLocked(oFileRef, False)
        else:
            mop.setShotCamLocked(oShotCam, False)

        try:
            mc.select(sCamAstGrp)
            sAbcPath = abcFile.absPath()
            mc.AbcImport(sAbcPath, mode="import", connect=sCamAstGrp)

            oAbcNode = self.getShotCamAbcNode()
            if oAbcNode:
                oAbcNode.setAttr("abc_File", abcFile.envPath())
                pc.lockNode(oAbcNode, lock=True)
        finally:
            if oFileRef:
                mop.setCamRefLocked(self.getShotCamera(), True)
            else:
                mop.setShotCamLocked(oShotCam, True)

        return oAbcNode

    @restoreSelection
    def editShotCam(self):

        oShotCam = self.getShotCamera()
        damShot = self.getDamShot()
        atomFile = damShot.getResource("public", "camera_atom", fail=True)

        sCamAstGrp = self.mkShotCamNamespace() + ":asset"
        oCamAstGrp = pc.PyNode(sCamAstGrp)

        oFileRef = oCamAstGrp.referenceFile()
        if oFileRef:
            bLocked = oFileRef.refNode.getAttr("locked")
            if bLocked:
                oShotCam = mop.setCamRefLocked(self.getShotCamera(), False)
        else:
            bLocked = oShotCam.isLocked()
            if bLocked:
                mop.setShotCamLocked(oShotCam, False)

        oAbcNode = self.getShotCamAbcNode()
        if oAbcNode:
            pc.lockNode(oAbcNode, lock=False)
            pc.delete(oAbcNode)
        elif not bLocked:
            pc.displayWarning("Shot camera is already edited.")
            return

        try:
            mc.select(sCamAstGrp)
            myasys.importAtomFile(atomFile.absPath(),
                                  targetTime="from_file",
                                  option="replace",
                                  match="string",
                                  selected="childrenToo")
        except:
            self.importShotCamAbcFile()
            raise

    def isShotCamEdited(self):

        if self.getShotCamAbcNode():
            return False

        oShotCam = self.getShotCamera()

        oFileRef = oShotCam.referenceFile()
        if oFileRef:
            return (not oFileRef.refNode.getAttr("locked")) and (not self.getShotCamAbcNode())
        else:
            return (not oShotCam.isLocked()) and (not self.getShotCamAbcNode())

    def showInShotgun(self):
        self.context['damProject']._shotgundb.showInBrowser(self.context['entity'])

    def logContext(self):

        from pprint import pprint

        print "pouet".center(100, "-")

        print "{}.{}:".format(type(self).__name__, "context")
        pprint(self.context, width=120)

        try:
            shotgundb = self.context['damProject']._shotgundb
        except Exception as e:
            print toStr(e)
        else:
            for k, pyobj in vars(shotgundb).iteritems():

                if "__" in k:
                    continue

                if k == "cmdtable":
                    continue

                if isinstance(pyobj, dict):
                    print "{}.{}:".format(type(shotgundb).__name__, k)
                    pprint(pyobj, width=120)

        print "prout".center(100, "-")

# capture
CAPTURE_INFOS = {}

def userInfo():
    return CAPTURE_INFOS['user']

def sceneInfo():
    return CAPTURE_INFOS['scene']

def stepInfo():
    return CAPTURE_INFOS['task']

def frameInfo():
    return pc.currentTime(query=True)

def cameraInfo():
    infos = (CAPTURE_INFOS['cam_file'],
             'F {}mm'.format(mc.getAttr(CAPTURE_INFOS['cam'] + '.focalLength')),)
    return " - ".join(s for s in infos if s)

def endFrameInfo():
    return CAPTURE_INFOS['end']

def createHUD():

    deleteHUD()
    headsUps = pc.headsUpDisplay(listHeadsUpDisplays=True)

    headUpsValues = {}
    for headsUp in headsUps:
        headUpsValues[headsUp] = pc.headsUpDisplay(headsUp, query=True, visible=True)
        pc.headsUpDisplay(headsUp, edit=True, visible=False)

    sSize = 'large'

    pc.headsUpDisplay('HUD_ZOMBUser', section=0, block=pc.headsUpDisplay(nextFreeBlock=0),
                      blockSize='small', label='', labelFontSize=sSize, dataFontSize=sSize,
                      command=userInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBScene', section=2, block=pc.headsUpDisplay(nextFreeBlock=2),
                      blockSize='small', label='', labelFontSize=sSize, dataFontSize=sSize,
                      command=sceneInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBStep', section=4, block=pc.headsUpDisplay(nextFreeBlock=4),
                      blockSize='small', label='', labelFontSize=sSize, dataFontSize=sSize,
                      command=stepInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBFrame', section=5, block=pc.headsUpDisplay(nextFreeBlock=5),
                      blockSize='small', label='', labelFontSize=sSize, dataFontSize=sSize,
                      command=frameInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBCam', section=7, block=pc.headsUpDisplay(nextFreeBlock=7),
                      blockSize='small', label='', labelFontSize=sSize, dataFontSize=sSize,
                      command=cameraInfo, attachToRefresh=True)
    pc.headsUpDisplay('HUD_ZOMBEndFrame', section=9, block=pc.headsUpDisplay(nextFreeBlock=9),
                      blockSize='small', label='', labelFontSize=sSize, dataFontSize=sSize,
                      command=endFrameInfo, attachToRefresh=True)

    return headUpsValues

def restoreHUD(oldValues=None):

    pc.headsUpDisplay('HUD_ZOMBUser', rem=True)
    pc.headsUpDisplay('HUD_ZOMBScene', rem=True)
    pc.headsUpDisplay('HUD_ZOMBStep', rem=True)
    pc.headsUpDisplay('HUD_ZOMBFrame', rem=True)
    pc.headsUpDisplay('HUD_ZOMBCam', rem=True)
    pc.headsUpDisplay('HUD_ZOMBEndFrame', rem=True)

    headsUps = pc.headsUpDisplay(listHeadsUpDisplays=True)

    if oldValues is not None:
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
            mc.headsUpDisplay(i, rem=True)


