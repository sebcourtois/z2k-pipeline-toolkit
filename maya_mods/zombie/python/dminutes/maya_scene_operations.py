
import os
import os.path as osp
import re
import shutil
from collections import namedtuple
from collections import OrderedDict
#from itertools import izip

import pymel.core as pc
import pymel.util as pmu
import maya.cmds as mc

from pytd.util.sysutils import toStr, inDevMode
from pytd.util.fsutils import jsonWrite, pathResolve, jsonRead

from pytaya.util.sysutils import withSelectionRestored
from pytaya.core.transform import matchTransform

from davos_maya.tool import reference as myaref
from zomblib.editing import makeFilePath, movieToJpegSequence
from dminutes.shotconformation import removeRefEditByAttr

pc.mel.source("AEimagePlaneTemplate.mel")

CAMPATTERN = 'cam_sq????_sh?????:*'
CAM_GLOBAL = 'Global_SRT'
CAM_LOCAL = 'Local_SRT'
CAM_DOLLY = 'Dolly'


def getNamespace(sNode):
    return sNode.rsplit("|", 1)[-1].rsplit(":", 1)[0]

def undoAtOnce(func):
    def doIt(*args, **kwargs):
        mc.undoInfo(openChunk=True)
        try:
            res = func(*args, **kwargs)
        finally:
            mc.undoInfo(closeChunk=True)
        return res
    return doIt

def withoutUndo(func):
    def doIt(*args, **kwargs):
        mc.undoInfo(stateWithoutFlush=False)
        try:
            res = func(*args, **kwargs)
        finally:
            mc.undoInfo(stateWithoutFlush=True)
        return res
    return doIt

STEREO_INFOS = {}
def recStereoInfos(frame, **kwargs):
    global STEREO_INFOS
    STEREO_INFOS[frame] = kwargs

def getStereoInfosRecorder(sStereoCam):

    import sys
    m = sys.modules["__main__"]
    m.mop = sys.modules[__name__]

    sExprCode = """
int $frame = frame;
float $sep = abs({camera}.stereoRightOffset);
float $conv = abs({camera}.filmBackOutputRight);
float $zero = {camera}.zeroParallax;
string $cmd = `format -s $frame -s $sep -s $conv -s $zero "mop.recStereoInfos(^1s, separation=^2s, convergence=^3s, zeroParallax=^4s)"`;
//print $cmd;
python($cmd);""".format(camera=sStereoCam)

    sName = "recorder_" + sStereoCam.rsplit(":", 1)[0].replace(":", "_")
    sExprNode = getNode(sName)
    if not sExprNode:
        sExprNode = mc.expression(n=sName, s=sExprCode, ae=True, uc="all")
    else:
        mc.expression(sExprNode, e=True, s=sExprCode, ae=True, uc="all")

    return sExprNode

def writeStereoInfos(sFilePath):

    global STEREO_INFOS

    if not STEREO_INFOS:
        raise RuntimeError("No stereo infos to write.")

    sDirPath = osp.dirname(sFilePath)
    if not osp.exists(sDirPath):
        os.makedirs(sDirPath)

    jsonWrite(sFilePath, STEREO_INFOS)

    return True

#0 as Maya CC, and 1 as OSD Uniform, 2 OSD adaptive
def setSubdivPref(i_inSubDiv=0):
    attrValue = i_inSubDiv
    if attrValue == 2:
        attrValue = 3
    elif attrValue == 1:
        attrValue = 2

    meshes = pc.ls(type='mesh', noIntermediate=True)
    for mesh in meshes:
        useGlobal = pc.getAttr('{0}.useGlobalSmoothDrawType'.format(mesh.name()))
        if useGlobal:
            pc.setAttr('{0}.smoothDrawType'.format(mesh.name()), attrValue)

    pc.polyOptions(newPolymesh=True, smoothDrawType=i_inSubDiv)

def getSceneContent(sceneManager):
    sceneContent = []

    #Collect references
    refs = pc.listReferences(namespaces=True)
    for ref in refs:
        ns = ref[0]
        path = ref[1]

        sceneContent.append({'name':'_'.join(ns.split("_")[:-1]), 'path':str(path)})

    return sceneContent

def getImagePlaneItems(create=False):

    oImgPlane = None
    oCamXfm = None

    oImgPlaneList = pc.ls("cam_animatic:assetShape->imgPlane_animatic")
    if oImgPlaneList:
        oImgPlane = oImgPlaneList[0]

    oCamList = pc.ls("cam_animatic:asset")
    if oCamList:
        oCamXfm = oCamList[0]

    if not oImgPlane:
        if not create:
            return oImgPlane, oCamXfm
        else:
            # - Create new Animatic Camera
            if not pc.namespace(exists='cam_animatic'):
                pc.namespace(addNamespace='cam_animatic')
            else:
                # - Remove previous Animatic Camera
                oCamList = pc.ls("cam_animatic:*")
                if oCamList:
                    pc.delete(oCamList)

            oCamXfm, oCamShape = pc.camera(name='cam_animatic:asset', aspectRatio=1.77, displayFilmGate=True)
            oCamXfm.rename('cam_animatic:asset')
            oCamShape.setAttr('visibility', 0)

            _, oImgPlane = pc.imagePlane(camera=oCamShape,
                                         showInAllViews=False,
                                         name="imgPlane_animatic")
            oImgPlane.rename("imgPlane_animatic")
    else:
        oCamXfm = oImgPlane.getParent(3)
        oCamShape = oCamXfm.getShape()

    if oCamXfm:
        sCamGrp = GRP_FOR_ASSET_TYPE["cam"]
        if mc.objExists(sCamGrp):
            oCamParent = oCamXfm.getParent()
            if (not oCamParent) or oCamParent.nodeName() != sCamGrp:
                pc.parent(oCamXfm, sCamGrp)

    #SET DE L'IMAGE PLANE
    sImgPlane = oImgPlane.name()
    pc.setAttr(sImgPlane + ".type", 0)
    pc.setAttr(sImgPlane + ".fit", 1)
    pc.setAttr(sImgPlane + ".useFrameExtension", 1)
    #pc.setAttr(sImgPlane + ".frameOffset", -100)
    #pc.setAttr(sImgPlane + ".frameIn", 101)
    #pc.setAttr(sImgPlane + ".frameOut", 1000)

    sCamShape = oCamShape.name()
    pc.setAttr(sCamShape + ".displayFilmGate", 1)
    pc.setAttr(sCamShape + ".displayGateMask", 1)
    pc.setAttr(sCamShape + ".overscan", 1.3)
    pc.setAttr(sCamShape + ".displaySafeTitle", 1)
    pc.setAttr(sCamShape + ".displaySafeAction", 1)
    pc.setAttr(sCamShape + ".displayGateMaskColor", [0, 0, 0])

    return oImgPlane, oCamXfm

def setImgPlaneHidden(bVisible):

    oImgPlaneList = pc.ls("imgPlane_animatic*", type="imagePlane")
    for oImgPlane in oImgPlaneList:
        try:
            oImgPlane.setAttr("hideOnPlayback", bVisible)
        except Exception as e:
            pc.displayWarning(toStr(e))

def isImgPlaneHidden():

    bVisible = False

    oImgPlaneList = pc.ls("imgPlane_animatic*", type="imagePlane")
    for oImgPlane in oImgPlaneList:
        oImgPlane.setAttr("visibility", True)
        bVisible = (bVisible or oImgPlane.getAttr("hideOnPlayback"))

    return bVisible

def importAsset(s_inPath, s_inNS='', b_inRef=True):
    importedAsset = None
    if b_inRef:
        importedAsset = pc.system.createReference(s_inPath, namespace=s_inNS)
    else:
        importedAsset = pc.system.importFile(s_inPath, namespace=s_inNS)

    return importedAsset

def removeAsset(s_inPath):
    mc.file(s_inPath, removeReference=True)

def getAssetRoot(s_inNS):
    assetRoot = None
    deprecatedMessage = 'Asset root name is obsolete ({0})'

    #try with "asset", this should be the right way
    roots = pc.ls('{0}:asset'.format(s_inNS))
    if len(roots) > 0:
        assetRoot = roots[0]
    else:
        #try with NS:NS, for 'old' assets
        roots = pc.ls('{0}:{0}'.format(s_inNS))
        if len(roots) > 0:
            assetRoot = roots[0]
            pc.warning(deprecatedMessage.format(assetRoot.name()))
        else:
            #try with NS:NS except '_default' if found, for 'older' assets
            oldRootName = '{0}:{1}'.format(s_inNS, s_inNS.replace('_default', ''))
            roots = pc.ls(oldRootName)
            if len(roots) > 0:
                assetRoot = roots[0]
                pc.warning(deprecatedMessage.format(assetRoot.name()))
            else:
                roots = pc.ls('{0}:{1}'.format(s_inNS, s_inNS.replace('Ref', '')))
                if len(roots) > 0:
                    assetRoot = roots[0]
                    pc.warning(deprecatedMessage.format(assetRoot.name()))
                else:
                    #try with NS:NS except '_default' if found, for 'older' assets
                    oldRootName = '{0}:{1}'.format(s_inNS, s_inNS.replace('_default', '').replace('Ref', ''))
                    roots = pc.ls(oldRootName)
                    if len(roots) > 0:
                        assetRoot = roots[0]
                        pc.warning(deprecatedMessage.format(assetRoot.name()))
                    else:
                        #try with NS:NS - last "_"
                        modifiedNS = "_".join(s_inNS.split("_")[:-1]) + "_previz"
                        if "_default" in modifiedNS:
                            modifiedNS = modifiedNS.replace('_default', '')

                        oldRootName = '{0}:{1}'.format(s_inNS, modifiedNS)
                        roots = pc.ls(oldRootName)
                        if len(roots) > 0:
                            assetRoot = roots[0]
                            pc.warning(deprecatedMessage.format(assetRoot.name()))

    return assetRoot

def getRoot(o_inObj):
    ns = o_inObj.namespace()
    obj = o_inObj
    objParent = obj.getParent()
    while(objParent != None and objParent.namespace() == ns):
        obj = objParent
        objParent = obj.getParent()

    return obj

GRP_FOR_ASSET_TYPE = {
'cam':'grp_camera',
'chr':'grp_character',
'set':'grp_set',
'prp':'grp_prop',
'env':'grp_environment',
'c2d':'grp_character2D',
'vhl':'grp_vehicle',
'fxp':'grp_fx',
'cwp':'grp_crowd',
}

def reArrangeAssets():
    #this is the template, it lacks grp_prop, grp_crowd, grp_vehicle, grp_fx, grp_light (and eventually grp_extra_rig, grp_trash)
    structure = GRP_FOR_ASSET_TYPE

    #Collect references
    refs = pc.listReferences(namespaces=True)

    for ref in refs:
        ns = ref[0]
        nsPrefix = ns.split('_')[0]
        for structKey in structure:
            structParent = structure[structKey]
            if structKey == nsPrefix:
                #Ok, we can rearrange this !
                root = getAssetRoot(ns)
                if not root:
                    #pc.warning("Can't find root of asset with namespace '{0}'".format(ns))
                    continue
                rootParent = root.getParent()
                if (not rootParent) or (rootParent.name() != structParent):
                    pc.parent(root, structParent)

    #We could also have local cameras (cam_animatic and/or cam_sq####_sh####)
    cams = pc.ls('*_cam_*:*', type='camera')
    for cam in cams:
        #print "cam " + str(cam)
        camRoot = getRoot(cam)
        #print "camRoot " + str(camRoot)
        camParent = camRoot.getParent()
        if camParent is None or camParent.name() != structure['cam']:
            #print camRoot, structure['cam']
            pc.parent(camRoot, structure['cam'])

def getCameraRig():
    camInfo = {}
    cams = pc.ls(CAMPATTERN, type='camera')

    if len(cams) == 0:
        pc.error("Can't find camera matching pattern '{0}'".format(CAMPATTERN))

    camInfo['Namespace'] = cams[0].namespace()
    camInfo['Shape'] = cams[0]
    camInfo['Transform'] = cams[0].getParent()

    camRoot = getRoot(cams[0])
    camInfo['Root'] = camRoot

    if mc.objExists(camInfo['Namespace'] + CAM_GLOBAL):
        camInfo['Global'] = pc.PyNode(camInfo['Namespace'] + CAM_GLOBAL)
    else:
        pc.error("Can't find global camera control with pattern '{0}'"
                 .format(camInfo['Namespace'] + CAM_GLOBAL))

    if mc.objExists(camInfo['Namespace'] + CAM_LOCAL):
        camInfo['Local'] = pc.PyNode(camInfo['Namespace'] + CAM_LOCAL)
    else:
        pc.error("Can't find local camera control with pattern '{0}'"
                 .format(camInfo['Namespace'] + CAM_LOCAL))

    if mc.objExists(camInfo['Namespace'] + CAM_DOLLY):
        camInfo['Dolly'] = pc.PyNode(camInfo['Namespace'] + CAM_DOLLY)
    else:
        pc.error("Can't find dolly camera control with pattern '{0}'"
                 .format(camInfo['Namespace'] + CAM_DOLLY))

    return camInfo

#GLOBALS METHODS
def canDo(s_inCommand, s_inTask):
    cmd = COMMANDS.get(s_inCommand)
    if cmd != None:
        return s_inTask in cmd

    return None

@undoAtOnce
def do(s_inCommand, s_inTask, sceneManager):
    cmd = COMMANDS.get(s_inCommand)
    if cmd == None:
        pc.error('Command "{0}" does not exists !'.format(s_inCommand))

    cmdCallable = cmd.get(s_inTask)
    if cmdCallable == None:
        pc.error('Process "{0}" does not exists for command "{1}" !'.format(s_inTask, s_inCommand))

    cmdBaseCallable = cmd.get('BASE')
    if cmdBaseCallable != None:
        cmdBaseCallable(sceneManager)
        #print '{} initialization done ! ({})'.format("base", sceneManager.context)

    cmdCallable(sceneManager)
    #print '{} initialization done ! ({})'.format(s_inTask, sceneManager.context)

def setMayaProject(sProjName):

    sMayaProjsLoc = osp.dirname(osp.normpath(mc.workspace(q=True, rd=True)))
    sMayaProjPath = osp.join(sMayaProjsLoc, sProjName)

    if not osp.exists(sMayaProjPath):
        os.mkdir(sMayaProjPath)

    mc.workspace(update=True)
    mc.workspace(sProjName, openWorkspace=True)

    if not mc.workspace(fileRuleEntry="movie"):
        mc.workspace(fileRule=("movie", "captures"))
        mc.workspace(saveWorkspace=True)

    if not mc.workspace(fileRuleEntry="alembicCache"):
        mc.workspace(fileRule=("alembicCache", "cache/alembic"))
        mc.workspace(saveWorkspace=True)

    pmu.putEnv("ZOMB_MAYA_PROJECT_PATH", sMayaProjPath.replace("\\", "/"))

    return sMayaProjPath

def getWipCaptureDir(damShot):

    p = osp.join(mc.workspace(fileRuleEntry="movie"),
                 damShot.sequence,
                 damShot.name,)

    return mc.workspace(expandName=p)

def getMayaCacheDir(damShot):

    p = osp.join(mc.workspace(fileRuleEntry="alembicCache"),
                 damShot.sequence,
                 damShot.name,)

    return mc.workspace(expandName=p)

def importSceneStructure(sceneManager):
    #Import only if does not exists...
    if pc.objExists('shot'):
        return

    sEntityType = sceneManager.context['entity']['type']

    #Import scene structure
    template_path = sceneManager.context['damProject'].getPath('template', 'project')
    strucure_path = osp.join(template_path, "{0}_layout_tree.ma".format(sEntityType.lower()))

    if osp.isfile(strucure_path):
        mc.file(strucure_path, i=True, rpr='')
    else:
        pc.warning("Base file structure not found for entity type : {0}".format(sEntityType))

def setCamAsPerspView(oCamXfm):
    perspPanel = mc.getPanel(withLabel='Persp View')
    pc.modelPanel(perspPanel, edit=True, camera=oCamXfm.getShape())

#Creates
def create_scene_base(sceneManager):
    mc.file(force=True, new=True)

    print 'base creation done ! ({0})'.format(sceneManager.context)

def create_previz_scene(sceneManager):
    sceneManager.updateSceneAssets()

    init_scene_base(sceneManager)
    setupShotScene(sceneManager)

    reArrangeAssets()

    #lock previz, save v001 in private, here ?
    privFile = sceneManager.edit(onBase=True)

    if privFile != None:
        #save the created file on the private
        pc.saveAs(privFile.absPath())

        print 'previz creation done ! ({0})'.format(sceneManager)
    else:
        print 'previz creation failed to Edit and save !'

def playbackTimesFromScene():

    times = dict(minTime=True,
                animationStartTime=True,
                maxTime=True,
                animationEndTime=True)

    for k, v in times.items():
        times[k] = pc.playbackOptions(q=True, **{k:v})

    return times

def init_scene_base(sceneManager):
    #Set units
    angle = 'degree'
    linear = 'centimeter'
    time = 'film'
    pc.currentUnit(angle=angle, linear=linear, time=time)

    #color management
    pc.colorManagementPrefs(edit=True, cmEnabled=False)

    #Swatches size
    mc.optionVar(iv=('maxImageSizeForSwatchGen', 1000))

    #Legacy Viewport textures
    mc.displayPref(maxTextureResolution=1024)

    #Viewport 2.0 textures
    mc.setAttr("hardwareRenderingGlobals.enableTextureMaxRes", 1)
    mc.setAttr("hardwareRenderingGlobals.textureMaxResolution", 1024)

    #entity specific initialisation
    if sceneManager.context['entity']['type'] == 'Shot':
        sceneManager.setPlaybackTimes()

    importSceneStructure(sceneManager)

def arrangeViews(oShotCam, oImgPlaneCam=None, oStereoCam=None,
                 singleView=False, stereoDisplay=""):

    # Set Viewport
    if singleView:
        pc.mel.eval('setNamedPanelLayout("Single Perspective View")')
    else:
        pc.mel.eval('setNamedPanelLayout("Four View")')
        pc.mel.eval('ThreeRightSplitViewArrangement')

    mc.refresh()

    if not singleView:
        #Image plane
        sideView = ""
        if oImgPlaneCam:
            sideView = mc.getPanel(withLabel='Side View')
            pc.modelEditor(sideView, edit=True, camera=oImgPlaneCam)

        #Work view
        workPanel = mc.getPanel(withLabel='Top View')
        pc.modelEditor(workPanel, edit=True, camera='persp')

        if sideView:
            pc.modelEditor(sideView, edit=True, allObjects=0, imagePlane=True, grid=False)

    #Camera
    perspView = mc.getPanel(withLabel='Persp View')
    pc.modelEditor(perspView, edit=True, camera=oShotCam)
    if oStereoCam:
        stereoPanel = "StereoPanel"
        mc.scriptedPanel(stereoPanel, e=True, rp=perspView)
        mc.stereoCameraView("StereoPanelEditor", e=True, rigRoot=oStereoCam.name())
        if stereoDisplay:
            mc.stereoCameraView("StereoPanelEditor", e=True, displayMode=stereoDisplay)
        perspView = "StereoPanelEditor"

    mc.modelEditor(perspView, e=True, activeView=True)
    mc.refresh()

def mkShotCamNamespace(sShotCode):
    return 'cam_{}'.format(sShotCode)

def getShotCamera(sShotCode, fail=False):

    sCamName = mkShotCamNamespace(sShotCode) + ":cam_shot_default"
    sCamList = mc.ls(sCamName)

    if not sCamList:
        if fail:
            raise RuntimeError("Shot Camera not found: '{}'".format(sCamName))
        return None

    if len(sCamList) == 1:
        return pc.PyNode(sCamList[0])
    else:
        raise RuntimeError("Multiple cameras named '{}'".format(sCamName))

def mkStereoCamNamespace(sShotCode):
    return "stereo_" + mkShotCamNamespace(sShotCode)

def getStereoCam(sShotCode, fail=False):

    sCamName = mkStereoCamNamespace(sShotCode) + ":cam_stereo"
    sCamList = mc.ls(sCamName)

    if not sCamList:
        if fail:
            raise RuntimeError("Stereo Camera not found: '{}'".format(sCamName))
        return None

    if len(sCamList) == 1:
        return pc.PyNode(sCamList[0])
    else:
        raise RuntimeError("Multiple cameras named '{}'".format(sCamName))

def addNode(sNodeType, sNodeName, parent=None, unique=True, skipSelect=True):
    if unique and mc.objExists(sNodeName):
        return sNodeName
    return mc.createNode(sNodeType, parent=parent, name=sNodeName, skipSelect=skipSelect)

def getNode(sNodeName):
    return sNodeName if mc.objExists(sNodeName) else None

def objectSetMembers(sSetName, recursive=True):

    if not mc.objExists(sSetName):
        return set()

    sMemberSet = mc.sets(sSetName, q=True)
    if sMemberSet is None:
        return set()
    else:
        sMemberSet = set(mc.ls(sMemberSet, dag=True, ni=True) if recursive else sMemberSet)

    return sMemberSet

def clearObjectSet(sSetName):
    mc.sets(e=True, clear=sSetName)

def addToSmoothSet(sSetName, in_sAddList):

    sMemberSet = objectSetMembers(sSetName)
    if sMemberSet:
        sAddSet = set(in_sAddList) - sMemberSet
    else:
        sAddSet = set(in_sAddList)

    if sAddSet:
        sAddList = list(sAddSet)
        mc.sets(sAddList, e=True, include=sSetName)

        sDagSet = set(mc.ls(sAddList, dag=True, ni=True))
        sDelSet = (sMemberSet & sDagSet) - sAddSet
        if sDelSet:
            mc.sets(list(sDelSet), e=True, remove=sSetName)

    return sAddSet

def addToSmooth():

    sSelList = mc.ls(sl=True, type="dagNode")
    if not sSelList:
        return

    sCurObjSet = addNode("objectSet", "set_applySmoothOnCapture", unique=True)
    addToSmoothSet(sCurObjSet, sSelList)

    sNoSmoothSet = getNode("set_ignoreSmoothOnCapture")
    if sNoSmoothSet:
        sCommonList = mc.sets(sNoSmoothSet, intersection=sCurObjSet)
        if sCommonList:
            sDelList = sCommonList + sSelList
        else:
            sDelList = sSelList
        mc.sets(sDelList, remove=sNoSmoothSet)
        smoothSetToRenderLayer(sNoSmoothSet)

    smoothSetToRenderLayer(sCurObjSet)

def delFromSmooth():

    sSelList = mc.ls(sl=True, type="dagNode")
    if not sSelList:
        return

    sCurObjSet = addNode("objectSet", "set_ignoreSmoothOnCapture", unique=True)
    addToSmoothSet(sCurObjSet, sSelList)

    sSmoothSet = getNode("set_applySmoothOnCapture")
    if sSmoothSet:

#        sDiffList = mc.sets(sCurObjSet, subtract=sSmoothSet)
#        print sDiffList

        sCommonList = mc.sets(sSmoothSet, intersection=sCurObjSet)
        if sCommonList:
            sDelList = list(set(sCommonList + sSelList))
        else:
            sDelList = sSelList
        mc.sets(sDelList, remove=sSmoothSet)
        smoothSetToRenderLayer(sSmoothSet)

    smoothSetToRenderLayer(sCurObjSet)

def listMeshesToSmooth():

    sMemberList = list(objectSetMembers("set_applySmoothOnCapture")
                       - objectSetMembers("set_ignoreSmoothOnCapture"))
    if not sMemberList:
        return []

    return mc.ls(sMemberList, type="mesh", ni=True)

def smoothSetToRenderLayer(sSetName):

    return

    sRndLyr = sSetName.replace("set_", "rlyr_")
    if not mc.objExists(sRndLyr):
        sRndLyr = mc.createRenderLayer(name=sRndLyr, empty=True)

    sLyrMemberSet = mc.editRenderLayerMembers(sRndLyr, q=True, fn=True)
    if sLyrMemberSet:
        sLyrMemberSet = set(mc.ls(sLyrMemberSet))
    else:
        sLyrMemberSet = set()

    sSetMemberSet = objectSetMembers(sSetName, recursive=False)

    sAddList = list(sSetMemberSet - sLyrMemberSet)
    if sAddList:
        mc.editRenderLayerMembers(sRndLyr, *sAddList, noRecurse=True)

    sDelList = list(sLyrMemberSet - sSetMemberSet)
    if sDelList:
        mc.editRenderLayerMembers(sRndLyr, *sDelList, remove=True, noRecurse=True)

def listSmoothableMeshes(project=None, warn=True):

    from pytaya.util import apiutils as myapi

    maxFaxes = pc.optionVar["smpSizeOfMeshForWarning"]
    nonSmoothableList = []


    sAllMeshSet = set(listMeshesToSmooth())
    numMeshes = len(sAllMeshSet)
    numFailure = 0

    sPrevizMeshSet = set(myaref.listPrevizRefMeshes(project=project))
    if sPrevizMeshSet:
        sCommonSet = sAllMeshSet & sPrevizMeshSet
        if sCommonSet:
            cmnLen = len(sCommonSet)
            nonSmoothableList.append(("{} meshes".format(cmnLen), "from a previz file."))

            numFailure = cmnLen - 1
            sAllMeshSet -= sCommonSet

    smoothData = OrderedDict()

    numAllFaces = 0
    for sMesh in sAllMeshSet:

        sSmoothAttr = sMesh + ".displaySmoothMesh"

        value = mc.getAttr(sSmoothAttr)
        if value == 2:
            continue

        if mc.getAttr(sSmoothAttr, lock=True):
            nonSmoothableList.append((sMesh, "'displaySmoothMesh' attribute is locked."))
            continue

        dagPath = myapi.getDagPath(sMesh)
        if not dagPath.isVisible():
            continue

        meshInfo = mc.polyEvaluate(sMesh, triangle=True, face=True)
        numFaces = meshInfo["face"]
        if numFaces == meshInfo["triangle"]:
            nonSmoothableList.append((sMesh, "fully triangulated."))
            continue

        if numFaces >= maxFaxes:
            nonSmoothableList.append((sMesh, ("has {:,} faces, limit is {:,} faces."
                                              .format(numFaces, maxFaxes))))
            continue

        if mc.polyInfo(sMesh, nonManifoldEdges=True, nonManifoldVertices=True):
            nonSmoothableList.append((sMesh, "non-manifold."))
            continue

        numAllFaces += numFaces

        meshInfo[".displaySmoothMesh"] = value
        smoothData[sMesh] = meshInfo

    if warn and nonSmoothableList:

        numFailure += len(nonSmoothableList)

        w = len(max((n for n, _ in nonSmoothableList), key=len))
        def fmt(n, m):
            return "{0:<{2}}: {1}".format(n, m, w)

        sSep = "\n- "
        sMsgHeader = " {}/{} meshes will not be smoothed. ".format(numFailure, numMeshes)
        sMsgBody = sSep.join(fmt(n, m) for n, m in nonSmoothableList)
        sMsgEnd = "".center(100, "-")

        sMsg = '\n' + sMsgHeader.center(100, "-") + sSep + sMsgBody + '\n' + sMsgEnd
        print sMsg

        pc.displayWarning(sMsgHeader + "More details in Script Editor ----" + (70 * ">"))

    return smoothData, numAllFaces

def getAnimaticInfos(sceneManager):

    sStepName = sceneManager.context["step"]["code"].lower()
    damShot = sceneManager.getDamShot()

    sRcName = "anim_capture" if sStepName == "final layout" else "animatic_capture"
    sPubMoviePath = damShot.getPath("public", sRcName)
    sLocMoviePath = osp.normpath(osp.join(getWipCaptureDir(damShot),
                                          osp.basename(sPubMoviePath)))
    sAnimaticImgPath = makeFilePath(osp.splitext(sLocMoviePath)[0],
                                    "animatic", "jpg", frame=1)
    sAudioPath = damShot.getPath("public", "animatic_sound")
    sAudioEnvPath = damShot.getLibrary().absToEnvPath(sAudioPath)

    File = namedtuple("File", ["path", "found"])

    infos = {"public_movie":sPubMoviePath,
            "local_movie":sLocMoviePath,
            "first_image":sAnimaticImgPath,
            "public_audio":sAudioEnvPath,
            }

    found = lambda p: osp.isfile(pathResolve(p))
    infos = dict((k, File(p, found(p))) for k, p in infos.iteritems())

    bNewerMovie = True
    if infos["public_movie"].found and infos["local_movie"].found:
        bNewerMovie = osp.getmtime(infos["public_movie"].path) > osp.getmtime(infos["local_movie"].path)

    infos["newer_movie"] = bNewerMovie

    return infos

def setupAnimatic(sceneManager, create=True, checkUpdate=False):

    oImgPlane, oImgPlaneCam = getImagePlaneItems(create=False)
    if (not create) and (not oImgPlaneCam):
        pc.displayError("Animatic camera not found: 'Shot Setup' needed.")
        return

    sErrorList = []
    sPanelList = tuple(iterPanelsFromCam(oImgPlaneCam)) if oImgPlaneCam else []
    bHidden = oImgPlane.getAttr("hideOnPlayback") if oImgPlane else False

    infos = getAnimaticInfos(sceneManager)

    sPubMoviePath = infos["public_movie"].path

    sAnimaticImgPath = ""
    if infos["public_movie"].found:

        sLocMoviePath = infos["local_movie"].path
        sAnimaticImgPath = infos["first_image"].path

        if oImgPlane:
            sCurImgPlanePath = pathResolve(oImgPlane.getAttr("imageName"))
            if osp.normcase(sCurImgPlanePath) != osp.normcase(sAnimaticImgPath):
                print "deleting", oImgPlaneCam
                pc.delete(oImgPlaneCam);pc.refresh()
                oImgPlane, oImgPlaneCam = None, None

        pc.currentTime(101);pc.refresh()
        bForce = False# if inDevMode() else False

        bUpdate = (infos["newer_movie"] or bForce)
        if bUpdate:
            sLocDirPath = osp.dirname(sLocMoviePath)
            if not osp.exists(sLocDirPath):
                os.makedirs(sLocDirPath)
            print "\nCopying '{}'\n     to '{}'".format(sPubMoviePath, sLocMoviePath)
            shutil.copy2(sPubMoviePath, sLocMoviePath)

        bImgSeqFound = infos["first_image"].found
        if bImgSeqFound and bUpdate:

            if oImgPlaneCam:
                print "deleting", oImgPlaneCam
                pc.delete(oImgPlaneCam);pc.refresh()
                oImgPlane, oImgPlaneCam = None, None

            print "deleting", osp.dirname(sAnimaticImgPath)
            shutil.rmtree(osp.dirname(sAnimaticImgPath), ignore_errors=False)

        if (not bImgSeqFound) or bUpdate:
            sImgSeqDirPath = osp.dirname(sAnimaticImgPath)
            if not osp.exists(sImgSeqDirPath):
                os.makedirs(sImgSeqDirPath)
            movieToJpegSequence(sLocMoviePath, sImgSeqDirPath, "animatic")
    else:
        sErrorList.append("Animatic movie not found: '{}'.".format(sPubMoviePath))

    if not (oImgPlaneCam and oImgPlane):
        oImgPlane, oImgPlaneCam = getImagePlaneItems(create=True)
        if sPanelList:
            for sPanel in sPanelList:
                pc.modelPanel(sPanel, e=True, camera=oImgPlaneCam)
        oImgPlane.setAttr("hideOnPlayback", bHidden)

    if oImgPlane and sAnimaticImgPath:
        try:
            pc.imagePlane(oImgPlane, edit=True, fileName=sAnimaticImgPath)
        except RuntimeError as e:
            if not "Unable to load the image file" in e.message:
                sErrorList.append(toStr(e))
        try:
            #offset +1 because ffmpeg duplicates the first frame during movie conversion to jpegs.
            oImgPlane.setAttr("frameOffset", (-100 + 1))
            pc.mel.AEimagePlaneViewUpdateCallback(oImgPlane.name())
        except Exception as e:
            pc.displayWarning(toStr(e))

    #son "Y:\shot\...\00_data\sqXXXX_shXXXXa_sound.wav"
    sAudioEnvPath = infos["public_audio"].path
    pc.mel.DeleteAllSounds()
    if infos["public_audio"].found:
        # --- Import Sound
        # - Import current shot Sound
        sAudioNode = pc.sound(offset=101, file=sAudioEnvPath, name='audio')

        # - Show Sound in Timeline
        aPlayBackSliderPython = pc.mel.eval('$tmpVar=$gPlayBackSlider')
        pc.timeControl(aPlayBackSliderPython, e=True, sound=sAudioNode, displaySound=True)
    else:
        sErrorList.append("Animatic sound not found: '{}'.".format(pathResolve(sAudioEnvPath)))

    if sErrorList:
        pc.displayError("\n" + "\n".join(sErrorList))

    return oImgPlane, oImgPlaneCam

@withSelectionRestored
def setupShotScene(sceneManager):

    # --- Set Viewport 2.0 AO default Value
    pc.setAttr('hardwareRenderingGlobals.ssaoAmount', 0.8)
    pc.setAttr('hardwareRenderingGlobals.ssaoRadius', 8)
    pc.setAttr('hardwareRenderingGlobals.ssaoFilterRadius', 8)
    pc.setAttr('hardwareRenderingGlobals.ssaoSamples', 16)

    sStepName = sceneManager.context["step"]["code"].lower()
    proj = sceneManager.context["damProject"]
    damShot = sceneManager.getDamShot()
    sShotCode = damShot.name

    if sStepName == "animation":

        if not pc.listReferences(loaded=True, unloaded=False):

            sAttrList = ("smoothDrawType", "displaySmoothMesh", "dispResolution")
            removeRefEditByAttr(attr=sAttrList, GUI=False)

            oAstRefList = myaref.loadAssetRefsToDefaultFile(project=proj, selected=False)

            for oFileRef in pc.listReferences(loaded=False, unloaded=True):
                if oFileRef in oAstRefList:
                    continue
                oFileRef.load()

    elif sStepName == "final layout":

        #bNoRefsAtAll = True if not pc.listReferences() else False
        bNoLoadedRefs = False#True if not pc.listReferences(loaded=True, unloaded=False) else False

        sAbcDirPath = getMayaCacheDir(damShot)
        if not osp.isdir(sAbcDirPath):
            raise EnvironmentError("Could not found caches directory: '{}'".format(sAbcDirPath))

        p = osp.normpath(osp.join(sAbcDirPath, "abcExport.json"))
        exportInfos = jsonRead(p)

        sNmspcList = tuple(getNamespace(j["root"]) for j in exportInfos["jobs"])
        myaref.importAssetRefsFromNamespaces(proj, sNmspcList, "render_ref")

        if bNoLoadedRefs:

            oFileRefList = pc.listReferences(loaded=False, unloaded=True)
            for oFileRef in oFileRefList:
                oFileRef.clean()

            myaref.loadAssetsAsResource("render_ref", project=proj, selected=False)

            for oFileRef in oFileRefList:
                if not oFileRef.isLoaded():
                    oFileRef.load()

            # optimize scene
            pmu.putEnv("MAYA_TESTING_CLEANUP", "1")
            sCleanOptList = ['nurbsSrfOption',
                             'ptConOption',
                             'pbOption',
                             'deformerOption',
                             'unusedSkinInfsOption',
                             'groupIDnOption',
                             'animationCurveOption',
                             'snapshotOption',
                             'unitConversionOption',
                             'shaderOption',
                             'displayLayerOption',
                             'renderLayerOption',
                             'setsOption',
                             'referencedOption',
                             'brushOption']
            try:
                pc.mel.scOpt_performOneCleanup(sCleanOptList)
            except Exception as e:
                pc.displayWarning(e.message)
                pmu.putEnv("MAYA_TESTING_CLEANUP", "")

    #rename any other shot camera
    remainingCamera = None

    sShotCamNspace = sceneManager.mkShotCamNamespace()

    otherCams = pc.ls(CAMPATTERN, type='camera')
    camsLength = len(otherCams)
    if camsLength > 0:
        if camsLength > 1:#Delete cameras except first
            for otherCam in otherCams:
                if camsLength == 1:
                    remainingCamera = otherCam
                    break
                sCamNs = otherCam.parentNamespace()
                if sShotCamNspace != sCamNs:
                    otherCam.setAttr("renderable", False)
                    #mc.setAttr(sCamNs + ":asset.visibility", False)
                    camsLength -= 1
        else:
            remainingCamera = otherCams[0]

        if remainingCamera and remainingCamera.parentNamespace() != sShotCamNspace:
            #rename camera
            pc.namespace(rename=(remainingCamera.namespace(), sShotCamNspace))


    oShotCam = sceneManager.getShotCamera()
    bCamAdded = False
    if not oShotCam:
        oShotCam = sceneManager.importShotCam()
        bCamAdded = True
    else:
        oCamRef = oShotCam.referenceFile()
        if oCamRef:
            bWasLocked = oCamRef.refNode.getAttr("locked")
            oShotCam = setCamRefLocked(oShotCam, False)
            oCamRef.importContents()
            setShotCamLocked(oShotCam, bWasLocked)

    sceneInfos = sceneManager.infosFromCurrentScene()
    bRcsMatchUp = sceneManager.resourcesMatchUp(sceneInfos)

    oStereoCam = None
    if sStepName != "previz 3d" and bRcsMatchUp:

        if sStepName == "layout":
            try:
                geomLayerL = mc.ls('*:geometry', type="displayLayer")
                for each in geomLayerL:
                    if not mc.getAttr(each + ".texturing"):
                        mc.setAttr(each + ".texturing", 1)
            except Exception as e:
                pc.displayWarning(toStr(e))

        if ((not sceneManager.isShotCamEdited()) or bCamAdded) and sceneManager.camAnimFilesExist():
            sceneManager.importShotCamAbcFile()

        oShotCam = sceneManager.getShotCamera(fail=True)

        if sStepName == "stereo":
            oStereoCam = getStereoCam(sShotCode, fail=False)
            if not oStereoCam:
                stereoCamFile = proj.getLibrary("public", "misc_lib").getEntry("layout/stereo_cam.ma")
                sImpNs = mkStereoCamNamespace(sShotCode)
                stereoCamFile.mayaImportScene(ns=sImpNs, returnNewNodes=False)
                oStereoCam = getStereoCam(sShotCode, fail=True)

            matchTransform(oStereoCam, oShotCam, atm="tr")
            pc.parentConstraint(oShotCam, oStereoCam, maintainOffset=True)
            oShotCam.attr("focalLength") >> oStereoCam.attr("focalLength")

    _, oAnimaticCam = setupAnimatic(sceneManager)

    reArrangeAssets()
    arrangeViews(oShotCam.getShape(), oAnimaticCam, oStereoCam, stereoDisplay="interlace")

COMMANDS = {
    'create':{
        'BASE':create_scene_base,
        'previz 3D':create_previz_scene,
    },
    'init':{
        'BASE':init_scene_base,
        'previz 3D':setupShotScene,
        'stereo':setupShotScene,
        'layout':setupShotScene,
        'animation':setupShotScene,
        'final layout':setupShotScene,
    }
}

def exportCamAlembic(**kwargs):

    timeRange = (pc.playbackOptions(q=True, animationStartTime=1),
                 pc.playbackOptions(q=True, animationEndTime=1))

    sFrameRange = " ".join((re.sub("0+$", "", "{:.4f}".format(t)).rstrip(".") for t in timeRange))

    sAbcJobArgs = """-frameRange {frameRange}
-attr horizontalFilmAperture
-attr verticalFilmAperture
-attr focalLength
-attr lensSqueezeRatio
-attr fStop
-attr focusDistance
-attr shutterAngle
-attr centerOfInterest
-dataFormat ogawa
-root {root}
-file {file}""".format(frameRange=sFrameRange, **kwargs)

    sHeader = " Alembic Export ".center(100, "-")
    print "\n", sHeader
    print sAbcJobArgs

    bImgPlnViz = isImgPlaneHidden()
    setImgPlaneHidden(False)
    try:
        res = mc.AbcExport(j=sAbcJobArgs.replace("\n", " "))
    finally:
        setImgPlaneHidden(bImgPlnViz)

    print sHeader

    return res

def switchShotCamToRef(scnMng, oShotCam):

    if oShotCam.isReferenced():
        raise RuntimeError("{} is already a reference.".format(oShotCam))

    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(suffix=".atom", delete=False) as f:
        sAtomFilePath = osp.normpath(f.name).replace("\\", "/")

    try:
        from pytaya.core import system as myasys

        sCamNs = oShotCam.parentNamespace()
        sCamAstGrp = sCamNs + ":asset"

        oCamAstGrp = pc.PyNode(sCamAstGrp)
        oParent = oCamAstGrp.getParent()

        mc.select(sCamAstGrp)
        myasys.exportAtomFile(sAtomFilePath,
                              SDK=True,
                              constraints=True,
                              animLayers=True,
                              statics=True,
                              baked=True,
                              points=False,
                              hierarchy="below",
                              channels="all_keyable",
                              timeRange="all",
                              )

        mc.namespace(rename=(sCamNs, sCamNs + "_OLD#"), parent=':')
        mc.refresh()

        sOldCamNs = oCamAstGrp.parentNamespace()
        oOldCam = pc.PyNode(sOldCamNs + ":cam_shot_default")
        oOldCam.getShape().setAttr("renderable", False)
        mc.setAttr(sOldCamNs + ":asset.visibility", False)

        oShotCam = scnMng.importShotCam()

        oCamAstGrp = pc.PyNode(sCamAstGrp)
        pc.parent(oCamAstGrp, oParent)

        mc.select(sCamAstGrp)
        myasys.importAtomFile(sAtomFilePath,
                              targetTime="from_file",
                              option="replace",
                              match="string",
                              selected="childrenToo")
    finally:
        os.remove(sAtomFilePath)

    return oShotCam

def setReferenceLocked(oFileRef, bLocked):

    oRefNode = oFileRef.refNode

    if oRefNode.getAttr("locked") != bLocked:

        bLoaded = oFileRef.isLoaded()

        if bLoaded:
            mc.file(unloadReference=oRefNode.name(), force=True)

        oRefNode.setAttr("locked", bLocked)

        if bLoaded:
            mc.file(loadReference=oRefNode.name())

def setCamRefLocked(oCam, bLocked):

    oFileRef = oCam.referenceFile()
    sCam = oCam.name()

    sCamShotPanelList = tuple(iterPanelsFromCam(oCam))
    setReferenceLocked(oFileRef, bLocked)
    oCam = pc.PyNode(sCam)
    if sCamShotPanelList:
        for sPanel in sCamShotPanelList:
            pc.modelPanel(sPanel, e=True, camera=oCam)
        pc.refresh()

    return oCam

def setShotCamLocked(oShotCam, bLocked):

#    sExcludeList = ("aspectRatio",
#                    "visibility",
#                    "filmOffset",
#                    "horizontalFilmOffset",
#                    "verticalFilmOffset",
#                    "preScale",
#                    "postProjection",
#                    "postScale",
#                    "nearClipPlane",
#                    "farClipPlane",
#                    "panZoomEnabled",
#                    "pan",
#                    "horizontalPan",
#                    "verticalPan",
#                    "zoom")

    sPattern = oShotCam.namespace() + "*"

    sAttrList = tuple((x + y) for x in "trs" for y in "xyz")

    for sObj in mc.ls(sPattern, type="transform"):

        mc.lockNode(sObj, lock=False)

        for sAttr in sAttrList:
            mc.setAttr(sObj + "." + sAttr, lock=bLocked)

        if bLocked:
            mc.lockNode(sObj, lock=True)


    sAttrList = ("focalLength", "horizontalFilmAperture", "verticalFilmAperture")

    for sObj in mc.ls(sPattern, type="camera"):

        mc.lockNode(sObj, lock=False)

        for sAttr in sAttrList:
            mc.setAttr(sObj + "." + sAttr, lock=bLocked)

        if bLocked:
            mc.lockNode(sObj, lock=True)


def saveDisplayLayersState():

    savedAttrs = {}

    for sLayer in mc.ls(type="displayLayer"):

        if sLayer.endswith("defaultLayer"):
            continue

        for sAttr in mc.listAttr(sLayer, settable=True, visible=True, scalar=True,
                                 unlocked=True):

            if sAttr == "identification":
                continue

            sNodeAttrName = sLayer + "." + sAttr
            try:
                savedAttrs[sNodeAttrName] = (mc.getAttr(sNodeAttrName),
                                             mc.getAttr(sNodeAttrName, type=True))
            except Exception as e:
                pc.displayWarning(toStr(e).rstrip())

    return savedAttrs

def restoreDisplayLayersState(savedAttrs):

    for sNodeAttrName, state in savedAttrs.iteritems():

        if not mc.objExists(sNodeAttrName):
            continue

        value, _ = state
        try:
            if value != mc.getAttr(sNodeAttrName):
                mc.setAttr(sNodeAttrName, value)
        except Exception as e:
            pc.displayWarning(toStr(e).rstrip())

def setGeometryLayersSelectable(bSelectable):

    value = 0 if bSelectable else 2

    for sLayer in mc.ls(type="displayLayer"):
        if not sLayer.endswith("geometry"):
            continue
        try:
            mc.setAttr(sLayer + "." + "displayType", value)
        except RuntimeError as e:
            pc.displayWarning(toStr(e).rstrip())

def iterPanelsFromCam(oCamXfm, visible=False):

    sCamXfm = oCamXfm.name()
    sCamShape = oCamXfm.getShape().name()

    sVizPanels = None
    if visible:
        sVizPanels = mc.getPanel(visiblePanels=True)

    for sPanel in mc.getPanel(type="modelPanel"):
        sPanelCam = mc.modelPanel(sPanel, q=True, camera=True)
        #print sPanel, sPanelCam, (sCamXfm, sCamShape)
        if sPanelCam in (sCamXfm, sCamShape):
            if sVizPanels and (sPanel not in sVizPanels):
                continue
            yield sPanel


