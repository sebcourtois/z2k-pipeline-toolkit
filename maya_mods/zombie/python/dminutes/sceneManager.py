#------------------------------------------------------------------
#               UI data and logic for sceneManagerUI.py
#------------------------------------------------------------------

import os
import re
import stat
import subprocess
from collections import OrderedDict

import pymel.core as pc
import maya.cmds as mc
import maya.mel

#import tkMayaCore as tkc
from pytd.util.fsutils import pathResolve, normCase, pathSuffixed
from pytd.util.logutils import logMsg

from davos.core import damproject
from davos.core.damtypes import DamShot, DamAsset
from davos_maya.tool.publishing import publishCurrentScene

from zomblib import shotgunengine

import dminutes.maya_scene_operations as mop
import dminutes.jipeLib_Z2K as jpZ
import dminutes.camImpExp as camIE
import dminutes.infoSetExp as infoE
#from dminutes.miscUtils import deleteUnknownNodes
from pytd.util.sysutils import toStr
from pytd.util.strutils import padded

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
                 'Layout':'layout_scene',
                 'Animation':'anim_scene',
                 }
RC_FOR_TASK = {}#{'previz 3D':'previz_scene', 'layout':'layout_scene'}

REF_FOR_STEP = {'Previz 3D':'previz_ref',
                'Layout':'anim_ref',
                'Animation':'anim_ref',
                }

REF_FOR_TASK = {}

LIBS = {'Asset':'asset_lib', 'Shot':'shot_lib'}

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

@restoreSelection
def makeCapture(filepath, start, end, width, height, displaymode="",
                showFrameNumbers=True, format="iff", compression="jpg",
                ornaments=False, play=False, useCamera=None, audioNode=None,
                i_inFilmFit=0, i_inDisplayResolution=0, i_inDisplayFilmGate=0,
                i_inOverscan=1.0, i_inSafeAction=0, i_inSafeTitle=0,
                i_inGateMask=0, f_inMaskOpacity=0.8, quick=False):

    pc.select(cl=True)
    names = []
    name = ""

    pan = pc.playblast(activeEditor=True)

    #Camera settings
    oldCamera = None
    if useCamera != None:
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
                           width=width, height=height,
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


    pc.setAttr(camera + ".filmFit", i_inFilmFit)
    pc.setAttr(camera + ".displayResolution", i_inDisplayResolution)
    pc.setAttr(camera + ".displayFilmGate", i_inDisplayFilmGate)
    pc.setAttr(camera + ".overscan", i_inOverscan)
    pc.setAttr(camera + ".displaySafeAction", i_inSafeAction)
    pc.setAttr(camera + ".displaySafeTitle", i_inSafeTitle)
    pc.setAttr(camera + ".displayGateMask", i_inGateMask)
    pc.setAttr(camera + ".displayGateMaskOpacity", f_inMaskOpacity)

    try:

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
        except Exception as e:
            pc.warning('damProject.getPath failed with {0}, {1}, {2} : {3}'.format(lib, s_inFileTag, tokens, e))

        return path

    def contextFromSceneInfos(self, sceneInfos):
        """format davos data to match with UI Data to allow detection of current loaded scene"""
        davosContext = {}
        proj = self.context['damProject']
        scnPathData = sceneInfos.get("path_data", {})
        #print "-------------", scnPathData
        if (("resource" not in scnPathData) or ("section" not in scnPathData)
            or ("name" not in scnPathData)):
            return None

        sSection = scnPathData["section"]
        if sSection == "shot_lib":

            sStepDir = scnPathData.get("step", "")
            if not sStepDir:
                return None

            sSgStepDct = proj.getVar("shot_lib", "sg_step_map")
            if sStepDir in sSgStepDct:
                davosContext['step'] = sSgStepDct[sStepDir]

            davosContext['seq'] = scnPathData["sequence"]
            davosContext['shot'] = scnPathData["name"]

        elif sSection == "asset_lib":
            pc.warning("asset_lib section not managed yet !!")
            return None
        else:
            pc.warning("Unknown section {0}".format(scnPathData["section"]))
            return None

        return davosContext

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

                data = proj.dataFromPath(sCurScnPath)
                infos["path_data"] = data
                infos["dam_entity"] = proj._entityFromPathData(data, fail=False)

        return infos

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

        ctxRcFile = self.entryFromContext()
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
        scnPubFile.assertEditedVersion(sceneInfos["priv_file"])
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
            if entry != None:
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

        if entry == None:
            entry = self.entryFromContext()

        if entry != None:
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

    def entryFromContext(self, fail=False):
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
                entry = damEntity.getResource("public", sRcName)
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

    def save(self, b_inForce=True):
        entry = self.entryFromContext()

        if entry == None:
            pc.error("Cannot get entry for context {0}".format(self.context))

        currentScene = os.path.abspath(pc.sceneName())
        if currentScene == '':
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

        return pc.saveAs(currentScene, force=b_inForce)

    def saveIncrement(self, b_inForce=True):
        # new incrementing system based on the last versoin present in the folder
        entry = self.entryFromContext()

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

    def getWipCaptureDir(self, damShot=None):

        if not damShot:
            damShot = self.getDamShot()

        p = osp.join(mc.workspace(fileRuleEntry="movie"),
                        damShot.sequence,
                        damShot.name,)

        return mc.workspace(expandName=p)

    def capture(self, increment=True, quick=True, sendToRv=False, smoothData=None):
        # BUG pas de son alors que son present dans la scene
        # BUG first frame decalee dupliquee dans les fichier output
        global CAPTURE_INFOS

        savedFile = None

        damShot = self.getDamShot()
        oShotCam = self.getShotCamera(fail=True)
        sShotCam = oShotCam.name()
        CAPTURE_INFOS['cam'] = oShotCam.getShape().name()
        oCamRef = oShotCam.referenceFile()

        sStep = self.context['step']['code']
        sTask = self.context['task']['content']

        if sStep.lower() == sTask.lower():
            CAPTURE_INFOS['task'] = sTask
        else:
            CAPTURE_INFOS['task'] = sStep + " | " + sTask

        CAPTURE_INFOS['user'] = self.context['damProject']._shotgundb.currentUser['name']

        sCamFile = ""
        if (not quick) and sStep.lower() != "previz 3d":

            sAbcPath = damShot.getPath("public", "camera_abc")
            abcFile = damShot.getLibrary()._weakFile(sAbcPath)

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

        CAPTURE_INFOS['cam_file'] = sCamFile#.rsplit(".", 1)[0]

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

        if not quick:
            if increment:
                savedFile = self.saveIncrement(b_inForce=False)
            else:
                savedFile = self.save(b_inForce=False)

            if savedFile is None:
                raise RuntimeError("Could not save current scene !")

        #Infer capture path
        scenePath = pc.sceneName()
        sFilename = os.path.basename(scenePath)
        CAPTURE_INFOS['scene'] = sFilename
        if not quick:
            sCapturePath = scenePath.replace(".ma", ".mov")
        else:
            sCapturePath = osp.join(self.getWipCaptureDir(damShot),
                                    sFilename.replace(".ma", ".mov"))
            maxIncr = 50
            def iterIncrementFiles(sFilePath, count):
                for i in xrange(1, count + 1):
                    p = pathSuffixed(sFilePath, "." + padded(i, 2))
                    try:
                        st = os.stat(p)
                    except OSError:
                        continue

                    if stat.S_ISREG(st.st_mode):
                        yield dict(path=p, mtime=st.st_mtime, num=i)

            incrementFiles = sorted(iterIncrementFiles(sCapturePath, maxIncr),
                                    key=lambda d:d["mtime"])
            if incrementFiles:
                incrFile = incrementFiles[-1]
                j = (incrFile["num"] % maxIncr) + 1
                sCapturePath = pathSuffixed(sCapturePath, "." + padded(j, 2))
            else:
                sCapturePath = pathSuffixed(sCapturePath, "." + padded(1, 2))

        if oCamRef:
            bWasLocked = oCamRef.refNode.getAttr("locked")
            mop.setReferenceLocked(oCamRef, False)

        bImgPlnViz = mop.isImgPlaneHidden()
        mop.setImgPlaneHidden(True)

        savedHudValues = createHUD()

        try:
            oShotCam = pc.PyNode(sShotCam)
            oShotCam.setAttr('aspectRatio', 1.85)

            _, oImgPlaneCam = mop.getImagePlaneItems(create=False)
            mop.arrangeViews(oShotCam, oImgPlaneCam)

            if smoothData:
                for sMesh in smoothData.iterkeys():
                    mc.setAttr(sMesh + ".displaySmoothMesh", 2)

            pc.refresh()

            makeCapture(sCapturePath, captureStart, captureEnd, 1280, 720, useCamera=oShotCam,
                        format="qt", compression="H.264", ornaments=True, play=False,
                        i_inFilmFit=1, i_inDisplayFilmGate=1, i_inSafeAction=1,
                        i_inSafeTitle=0, i_inGateMask=1, f_inMaskOpacity=1.0, quick=quick)
        finally:
            if smoothData:
                for sMesh, meshInfo in smoothData.iteritems():
                    for k, v in meshInfo.iteritems():
                        if k.startswith("."):
                            mc.setAttr(sMesh + k, v)

            oShotCam.setAttr('aspectRatio', 1.7778)

            if oCamRef and bWasLocked:
                mop.setReferenceLocked(oCamRef, True)
                oShotCam = pc.PyNode(sShotCam)
                mop.setCamAsPerspView(oShotCam)

            restoreHUD(savedHudValues)

            mop.setImgPlaneHidden(bImgPlnViz)

        sCmd = ""
        bShell = False

        if sendToRv:
            p = r"C:\Program Files\Shotgun\RV 6.2.6\bin\rvpush.exe"
            if osp.isfile(p):
                sLauncherLoc = osp.dirname(os.environ["Z2K_LAUNCH_SCRIPT"])
                p = osp.join(sLauncherLoc, "rvpush.bat")
                sCmd = p + " -tag playblast merge {}"
            else:
                pc.displayError("Could not send capture to RV. Missing app: '{}'".format(p))

        if not sCmd:
            sCmd = "start {}"
            bShell = True

        sCmd = sCmd.format(sCapturePath.replace("/", "\\"))
        subprocess.call(sCmd, shell=bShell)

    def edit(self, editInPlace=None, onBase=False, createFolders=False):
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
            if createFolders:
                msg = ("Entity '{0}' does not exists, do yout want to create it ?"
                       .format(damEntity.name))
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

        bPreviz = self.context["step"]["code"].lower() == "previz 3d"

        # here is incerted the publish of the camera of the scene
        print "exporting the camera of the shot"
        camImpExpI = camIE.camImpExp()
        camImpExpI.exportCam(sceneName=jpZ.getShotName())

        # here is the publish of the infoSet file with the position of the global and local srt of sets assets
        infoSetExpI = infoE.infoSetExp()
        infoSetExpI.export(sceneName=jpZ.getShotName())

        if (not bPreviz) and self.isShotCamEdited():
            self.exportCamAnimFiles()
            self.importShotCamAbcFile()
            mop.setCamAsPerspView(self.getShotCamera())

    def publish(self):

        proj = self.context['damProject']

        currentScene = os.path.abspath(pc.sceneName())
        if currentScene != '':
            entry = proj.entryFromPath(currentScene)
            if entry == None:
                pc.error()

            sFixMsg = " Please, apply a 'Shot Setup' and retry."
            oShotCam = None
            try:
                oShotCam = self.getShotCamera(fail=True)
            except RuntimeError as e:
                raise RuntimeError(toStr(e) + sFixMsg)

            if self.context["step"]["code"].lower() != "previz 3d":
                if not oShotCam.isReferenced():
                    raise RuntimeError("Shot Camera is not referenced !" + sFixMsg)

            rslt = publishCurrentScene(dependencies=False,
                                       prePublishFunc=self.prePublishCurrentScene)
            if rslt is None:
                return

            # here is the original publish
            if rslt is not None:
                pc.confirmDialog(title='Publish OK', message='{0} was published successfully'.format(rslt[0].name))
        else:
            pc.error("Please save your scene as a valid private working scene (Edit if needed)")

    def getShotgunContent(self):
        #print 'getShotgunContent ' + self.context['entity']['code']
        content = self.context['damProject']._shotgundb.getShotAssets(self.context['entity']['code'])
        return content if content != None else []

    def getFileTagFromPath(self, in_sPath):
        """Detect the filetag (resource) from an asset path, when we don't have the shotgun info, right now it'll just say 'NONE'"""
        return notFoundvalue

    def listRelatedAssets(self):
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
            drcLib = damAst.getLibrary()
            astRcDct = {}

            entryFromPath = lambda p: proj.entryFromPath(p, library=drcLib, dbNode=False)
            mayaRcIter = damAst.iterMayaRcItems(filter="*_ref")
            mayaFileItems = tuple((n, entryFromPath(p)) for n, p in mayaRcIter)

            #proj.dbNodesForResources(tuple(f for _, f in mayaFileItems if f))

            for sRcName, mrcFile in mayaFileItems:

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
                errorTxt = "{0}: {1}".format(astData['name'], err)
                print errorTxt
                errorL.append(errorTxt)
            else:
                count += 1

        if count:
            mop.reArrangeAssets()

        if len(errorL):
            mc.confirmDialog(title='Error',
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

        assetDataList = self.listRelatedAssets()
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

    def mkShotCamNamespace(self):
        return mop.mkShotCamNamespace(self.context['entity']['code'].lower())

    def getShotCamera(self, fail=False):
        return mop.getShotCamera(self.context['entity']['code'].lower(), fail=fail)

    def importShotCam(self):

        sCamNspace = self.mkShotCamNamespace()
        if mc.namespace(exists=sCamNspace):
            raise RuntimeError("Namespace already exists: '{}'".format(sCamNspace))

        damCam = self.context["damProject"].getAsset("cam_shot_default")
        camFile = damCam.getResource("public", "scene")
        camFile.mayaImportScene(ns=sCamNspace)
        mc.refresh()

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

        #damShot = self.getDamShot()

        #sFileName = os.path.basename(damShot.getPath("public", "camera_abc"))
        #sAbcNodeName = os.path.splitext(sFileName)[0] + "_AlembicNode"

        sShotCamNs = self.mkShotCamNamespace()

        def iterFuture(sAbcNode):
            sFutureList = mc.listHistory(sAbcNode, future=True)
            if sFutureList is not None:
                for sNode in sFutureList:
                    if sNode != sAbcNode and sNode.startswith(sShotCamNs + ":"):
                        yield sNode

        sAbcNodeList = []
        for sAbcNode in mc.ls(type="AlembicNode"):

            sFuturList = tuple(iterFuture(sAbcNode))
            if not sFuturList:
                mc.lockNode(sAbcNode, lock=False)
                print "delete unused '{}'".format(sAbcNode)
                mc.delete(sAbcNode)
            else:
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

    def exportCamAnimFiles(self, publish=True):

        from pytaya.core import system as myasys

        damShot = self.getDamShot()

        sPubAtomPath = damShot.getPath("public", "camera_atom")
        sPubAbcPath = damShot.getPath("public", "camera_abc")

        oCamAstGrp = pc.PyNode(self.mkShotCamNamespace() + ":asset")

        mop.init_shot_constants(self)

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

            sFilePathItems = ((sPrivAtomPath, sPubAtomPath), (sPrivAbcPath, sPubAbcPath))
            for sPrivPath, sPubPath  in sFilePathItems:
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

        if oFileRef:
            mop.setReferenceLocked(oFileRef, False)

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
                mop.setReferenceLocked(oFileRef, True)
                mop.setCamAsPerspView(self.getShotCamera())

        return oAbcNode

    def editShotCam(self):

        from pytaya.core import system as myasys

        damShot = self.getDamShot()
        atomFile = damShot.getResource("public", "camera_atom", fail=True)

        sCamAstGrp = self.mkShotCamNamespace() + ":asset"
        oCamAstGrp = pc.PyNode(sCamAstGrp)
        oFileRef = oCamAstGrp.referenceFile()
        if oFileRef:

            bLocked = oFileRef.refNode.getAttr("locked")
            if bLocked:
                mop.setReferenceLocked(oFileRef, False)
                mop.setCamAsPerspView(self.getShotCamera())

            oAbcNode = self.getShotCamAbcNode()
            if oAbcNode:
                pc.lockNode(oAbcNode, lock=False)
                pc.delete(oAbcNode)
            elif not bLocked:
                pc.displayWarning("Shot camera is already editable.")
                return

            try:
                pc.select(sCamAstGrp)
                myasys.importAtomFile(atomFile.absPath(),
                                      targetTime="from_file",
                                      option="replace",
                                      match="string",
                                      selected="childrenToo")
            except:
                self.importShotCamAbcFile()
                raise
        else:
            pc.displayWarning("Shot camera is not referenced !")
            return

    def isShotCamEdited(self):

        if self.getShotCamAbcNode():
            return False

        sCamAstGrp = self.mkShotCamNamespace() + ":asset"
        oCamAstGrp = pc.PyNode(sCamAstGrp)

        oFileRef = oCamAstGrp.referenceFile()
        if oFileRef:
            return (not oFileRef.refNode.getAttr("locked")) and (not self.getShotCamAbcNode())
        else:
            return True

    def showInShotgun(self):
        self.context['damProject']._shotgundb.showInBrowser(self.context['entity'])

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
            mc.headsUpDisplay(i, rem=True)


