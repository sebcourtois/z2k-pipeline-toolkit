
import os
import os.path as osp
import re
import shutil
from collections import namedtuple
from collections import OrderedDict
#from itertools import izip
import traceback

import pymel.core as pc
#import pymel.util as pmu
import maya.cmds as mc

from pytd.util.sysutils import toStr
from pytd.util.fsutils import jsonWrite, pathResolve, jsonRead, copyFile

from zomblib.editing import makeFilePath, movieToJpegSequence

from pytaya.core.general import copyAttrs, getObject
from pytaya.core import system as myasys
from pytaya.core.transform import matchTransform
from davos_maya.tool import reference as myaref

from dminutes.miscUtils import deleteUnknownNodes

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

def withErrorDialog(func):
    def doIt(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        except Warning:
            raise
        except Exception as e:
            pc.confirmDialog(title='SORRY !',
                             message=toStr(e),
                             button=["OK"],
                             defaultButton="OK",
                             cancelButton="OK",
                             dismissString="OK",
                             icon="critical")
            raise
        return res
    return doIt

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

def promptToContinue(exception):

    res = pc.confirmDialog(title='WARNING !',
                           message=exception.message,
                           button=['Continue', 'Abort'],
                           defaultButton='Abort',
                           cancelButton='Abort',
                           dismissString='Abort',
                           icon="warning")
    if res == "Abort":
        raise RuntimeWarning("Aborted !")

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

def setSubdivPref(i_inSubDiv=0):
    """0 as Maya CC, and 1 as OSD Uniform, 2 OSD adaptive"""
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
        gPlayBackSlider = pc.mel.eval('$tmpVar=$gPlayBackSlider')
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

def importSceneStructure(sEntityType, sTemplateDirPath):
    sStructScnPath = osp.join(sTemplateDirPath, "{0}_layout_tree.ma".format(sEntityType.lower()))
    if osp.isfile(sStructScnPath):
        mc.file(sStructScnPath, i=True, rpr='')
    else:
        pc.warning("Base file structure not found for entity type : {0}".format(sEntityType))

def setCamAsPerspView(oCamXfm):
    perspPanel = mc.getPanel(withLabel='Persp View')
    pc.modelPanel(perspPanel, edit=True, camera=oCamXfm.getShape())

def playbackTimesFromScene():

    times = dict(minTime=True,
                animationStartTime=True,
                maxTime=True,
                animationEndTime=True)

    for k, v in times.items():
        times[k] = pc.playbackOptions(q=True, **{k:v})

    return times

def init_scene_base():
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

    # --- Set Viewport 2.0 AO default Value
    pc.setAttr('hardwareRenderingGlobals.ssaoAmount', 0.8)
    pc.setAttr('hardwareRenderingGlobals.ssaoRadius', 8)
    pc.setAttr('hardwareRenderingGlobals.ssaoFilterRadius', 8)
    pc.setAttr('hardwareRenderingGlobals.ssaoSamples', 16)

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

def mkOldStereoCamNamespace(sShotCode):
    return "stereo_" + mkShotCamNamespace(sShotCode)

def getOldStereoCam(sShotCode, fail=False):
    sCamName = mkOldStereoCamNamespace(sShotCode) + ":cam_stereo"
    try:
        oStereoCam = pc.PyNode(sCamName)
    except pc.MayaNodeError:
        if fail:
            raise
        return None

    return oStereoCam

def mkStereoCamNamespace():
    return "stereo_rig"

def getStereoCam(sShotCode="", fail=False):

    sCamNspc = mkStereoCamNamespace()

    if sShotCode:
        oStereoCam = getOldStereoCam(sShotCode, fail=False)
        if oStereoCam:
            oFileRef = oStereoCam.referenceFile()
            if oFileRef:
                oFileRef.namespace = sCamNspc
            else:
                sNamespace = oStereoCam.parentNamespace()
                pc.namespace(rename=(sNamespace, sCamNspc), parent=':')

    sCamName = sCamNspc + ":cam_stereo"
    try:
        oStereoCam = pc.PyNode(sCamName)
    except pc.MayaNodeError:
        if fail:
            raise
        return None

    return oStereoCam

def loadStereoCam(damShot, withAnim=True):

    proj = damShot.project
    sShotCode = damShot.name

    oShotCam = getShotCamera(sShotCode, fail=True)
    oStereoCam = getStereoCam(sShotCode, fail=False)
    sStereoNs = mkStereoCamNamespace()

    if not oStereoCam:
        stereoCamFile = proj.getLibrary("public", "misc_lib").getEntry("layout/stereo_cam.ma")
        stereoCamFile.mayaImportScene(ns=sStereoNs, returnNewNodes=False)
        oStereoCam = getStereoCam(fail=True)
    
    oStereoCamShape = oStereoCam.getShape()
    sStereoGrp = getObject(sStereoNs + ":grp_stereo", fail=True)
    try:
        mc.parent(sStereoGrp, "|shot|grp_camera")
    except Exception as e:
        pc.displayWarning(e.message)

    try:
        if withAnim:
            atomFile = damShot.getResource("public", "stereoCam_anim", fail=True)
            if atomFile:
                mc.select(sStereoGrp)
                myasys.importAtomFile(atomFile.absPath(),
                                      targetTime="from_file",
                                      option="replace",
                                      match="string",
                                      search=mkOldStereoCamNamespace(sShotCode) + ":",
                                      replace=sStereoNs + ":",
                                      selected="childrenToo")
                
                sAtomFixCamShape = sStereoNs + ":atomFix_" + oStereoCamShape.nodeName(stripNamespace=True)
                sAtomFixCamShape = getObject(sAtomFixCamShape, fail=True)
                sAttrList = pc.listAttr(sAtomFixCamShape, k=True)
                sAttrList = copyAttrs(sAtomFixCamShape, oStereoCamShape, *sAttrList,
                                      create=False, values=True, inConnections=True)

    except Exception as e:
        traceback.print_exc()
        pc.displayError("Failed importing animation on '{}' from '{}'"
                        .format(sStereoGrp, atomFile.absPath()))
    finally:
        matchTransform(oStereoCam, oShotCam, atm="tr")
        pc.parentConstraint(oShotCam, oStereoCam, maintainOffset=True)
        oShotCam.attr("focalLength") >> oStereoCam.attr("focalLength")
        oShotCam.attr("cameraAperture") >> oStereoCam.attr("cameraAperture")

    return oStereoCam

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

def getAnimaticInfos(damShot, sSgStep):

    sStepName = sSgStep.lower()

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
    infos["frameOffset"] = (-99 if sRcName == "animatic_capture" else -100)
    infos["sound_enabled"] = False if sStepName in ("rendering",) else True

    return infos

def setupAnimatic(animaticInfos, create=True):

    oImgPlane, oImgPlaneCam = getImagePlaneItems(create=False)
    if (not create) and (not oImgPlaneCam):
        pc.displayError("Animatic camera not found: 'Shot Setup' needed.")
        return

    sErrorList = []
    sPanelList = tuple(iterPanelsFromCam(oImgPlaneCam)) if oImgPlaneCam else []
    bHidden = oImgPlane.getAttr("hideOnPlayback") if oImgPlane else False

    infos = animaticInfos
    bWithSound = animaticInfos["sound_enabled"]

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
            oImgPlane.setAttr("frameOffset", infos["frameOffset"])
            pc.mel.AEimagePlaneViewUpdateCallback(oImgPlane.name())
        except Exception as e:
            pc.displayWarning(toStr(e))

    #son "Y:\shot\...\00_data\sqXXXX_shXXXXa_sound.wav"
    sAudioEnvPath = infos["public_audio"].path
    if mc.objExists("audio"):
        mc.delete("audio")
    if infos["public_audio"].found:
        # --- Import Sound
        # - Import current shot Sound
        sAudioNode = pc.sound(offset=101, file=sAudioEnvPath, name="audio")

        # - Show Sound in Timeline
        if bWithSound:
            aPlayBackSliderPython = pc.mel.eval('$tmpVar=$gPlayBackSlider')
            pc.timeControl(aPlayBackSliderPython, e=True, sound=sAudioNode, displaySound=True)
    else:
        sErrorList.append("Animatic sound not found: '{}'.".format(pathResolve(sAudioEnvPath)))

    if sErrorList:
        pc.displayError("\n" + "\n".join(sErrorList))

    return oImgPlane, oImgPlaneCam

def initShotSceneFrom(damShot, sCurScnRc, sSrcScnRc, **kwargs):

    curPubScn = damShot.getResource("public", sCurScnRc, dbNode=False, fail=True)
    srcPubScn = damShot.getResource("public", sSrcScnRc, dbNode=False, fail=True)

    curPubScnVers = curPubScn.assertLatestFile(refresh=True, returnVersion=True)
    if curPubScnVers:
        err = AssertionError("{} - '{}' already started (v{})."
                             .format(damShot, sCurScnRc, curPubScn.currentVersion))
        promptToContinue(err)

    sLockOwner = srcPubScn.getLockOwner(refresh=True)
    if sLockOwner:
        raise AssertionError("{} - '{}' locked by '{}'".format(damShot, sSrcScnRc, sLockOwner))

    srcPubScnVers = srcPubScn.assertLatestFile(refresh=False, returnVersion=True)
    if not srcPubScnVers:
        raise AssertionError("{} - No '{}' version found".format(damShot, sSrcScnRc))

    sCurScnPath = pc.sceneName()
    copyFile(srcPubScnVers.absPath(), sCurScnPath)
    myasys.openScene(sCurScnPath, force=True, fail=False, **kwargs)

    try:
        deleteUnknownNodes()
    except Exception as e:
        pc.displayInfo(e)

    pc.refresh()

def assertTaskIsFinal(damShot, sTask, step="", sgEntity=None, critical=True):

    sgTask = damShot.getSgTask(sTask, step, sgEntity=sgEntity, fail=True)
    if sgTask["sg_status_list"] == "fin":
        return True

    err = AssertionError("Status of the {} task is not final yet."
                         .format("|".join(s for s in (step, sTask) if s)))
    if critical:
        raise err

    promptToContinue(err)

def loadRenderRefsFromCaches(damShot, sSpace):

    proj = damShot.project

    if sSpace == "local":
        sCacheDirPath = getMayaCacheDir(damShot)
    elif sSpace in ("public", "private"):
        sCacheDirPath = damShot.getPath(sSpace, "finalLayout_cache_dir")
    else:
        raise ValueError("Invalid space argument: '{}'".format(sSpace))

    if not osp.isdir(sCacheDirPath):
        raise EnvironmentError("Could not found {} caches directory: '{}'"
                               .format(sSpace, sCacheDirPath))

    p = osp.normpath(osp.join(sCacheDirPath, "abcExport.json"))
    exportInfos = jsonRead(p)

    sNmspcList = tuple(getNamespace(j["root"]) for j in exportInfos["jobs"])
    return myaref.importAssetRefsFromNamespaces(proj, sNmspcList, "render_ref")

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

    sMsgHeader = " Alembic Export ".center(100, "-")
    print "\n", sMsgHeader
    print sAbcJobArgs

    bImgPlnViz = isImgPlaneHidden()
    setImgPlaneHidden(False)
    try:
        res = mc.AbcExport(j=sAbcJobArgs.replace("\n", " "))
    finally:
        setImgPlaneHidden(bImgPlnViz)

    print sMsgHeader

    return res

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


