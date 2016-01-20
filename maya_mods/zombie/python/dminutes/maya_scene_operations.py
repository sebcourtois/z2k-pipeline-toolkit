
import os
import re
from functools import partial

import pymel.core as pc
import maya.cmds as mc
from pytd.util.sysutils import toStr

from pytaya.core.reference import listReferences
from davos_maya.tool.reference import listMayaRcForSelectedRefs
from davos_maya.tool.general import entityFromScene
#from pytd.util.strutils import upperFirst
from PySide import QtGui, QtCore


CAMPATTERN = 'cam_sq????_sh?????:*'
CAM_GLOBAL = 'Global_SRT'
CAM_LOCAL = 'Local_SRT'
CAM_DOLLY = 'Dolly'


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
    IMGP = None

    IMGPs = pc.ls("cam_animatic:assetShape->imgPlane_animatic*")
    if len(IMGPs) > 0:
        IMGP = IMGPs[0]

    if (not IMGP) and (not create):
        return None, None

    cam_animatic = pc.ls("cam_animatic:*")
    if len(cam_animatic) > 0:
        return (IMGP, cam_animatic[0])
    else:
        if create:
            pc.delete(IMGP)
        else:
            return None, None

    # - Remove previous Animatic Camera
    cam_animatic = pc.ls("cam_animatic:*")
    if len(cam_animatic) > 0:
        pc.delete(cam_animatic)

    # - Create new Animatic Camera
    if not pc.namespace(exists='cam_animatic'):
        pc.namespace(addNamespace='cam_animatic')

    cam_animatic = pc.camera(name='cam_animatic:asset', aspectRatio=1.77, displayFilmGate=True)
    cam_animatic[0].rename('cam_animatic:asset')
    pc.setAttr(cam_animatic[1].name() + '.visibility', 0)
    #mc.parent( CAM_Animatic[0], grpDict['GD_ROOT'] )

    IMGP = pc.imagePlane(camera=cam_animatic[1], showInAllViews=False, name="imgPlane_animatic")
    IMGP[1].rename("imgPlane_animatic")

    #SET DE L'IMAGE PLANE
    pc.setAttr(IMGP[1].name() + ".type", 2)
    pc.setAttr(IMGP[1].name() + ".fit", 1)
    pc.setAttr(IMGP[1].name() + ".useFrameExtension", 1)
    pc.setAttr(IMGP[1].name() + ".frameOffset", -100)
    pc.setAttr(IMGP[1].name() + ".frameIn", 101)
    pc.setAttr(IMGP[1].name() + ".frameOut", 1000)
    pc.setAttr(cam_animatic[1] + ".displayFilmGate", 1)
    pc.setAttr(cam_animatic[1] + ".displayGateMask", 1)
    pc.setAttr(cam_animatic[1] + ".overscan", 1.4)
    pc.setAttr(cam_animatic[1] + ".displaySafeTitle", 1)
    pc.setAttr(cam_animatic[1] + ".displaySafeAction", 1)
    pc.setAttr(cam_animatic[1] + ".displayGateMaskColor", [0, 0, 0])

    return (IMGP[1], cam_animatic[0])

def setImgPlaneVisible(bVisible):

    oImgPlaneList = pc.ls("imgPlane_animatic*", type="imagePlane")
    for oImgPlane in oImgPlaneList:
        try: oImgPlane.setAttr("visibility", bVisible)
        except Exception as e: pc.displayWarning(toStr(e))

def isImgPlaneVisible():

    bVisible = False

    oImgPlaneList = pc.ls("imgPlane_animatic*", type="imagePlane")
    for oImgPlane in oImgPlaneList:
        bVisible = (bVisible or oImgPlane.getAttr("visibility"))

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

def reArrangeAssets():
    #this is the template, it lacks grp_prop, grp_crowd, grp_vehicle, grp_fx, grp_light (and eventually grp_extra_rig, grp_trash)
    structure = {
        'cam':'grp_camera',
        'chr':'grp_character',
        'set':'grp_set',
        'prp':'grp_prop',
        'env':'grp_environment',
        'c2d':'grp_character2D',
        'vhl':'grp_vehicle',
        }

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
                if root == None:
                    pc.warning('Can"t find root of asset with namespace {0}'.format(ns))
                    continue
                rootParent = root.getParent()
                if rootParent == None or rootParent.name() != structParent:
                    pc.parent(root, structParent)

    #We could also have local cameras (cam_animatic and/or cam_sq####_sh####)
    cams = pc.ls('cam_*:*', type='camera')
    for cam in cams:
        #print "cam " + str(cam)
        camRoot = getRoot(cam)
        #print "camRoot " + str(camRoot)
        camParent = camRoot.getParent()
        if camParent == None or camParent.name() != structure['cam']:
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
        pc.error("Can't find global camera control with pattern '{0}'".format(camInfo['Namespace'] + CAM_GLOBAL))

    if mc.objExists(camInfo['Namespace'] + CAM_LOCAL):
        camInfo['Local'] = pc.PyNode(camInfo['Namespace'] + CAM_LOCAL)
    else:
        pc.error("Can't find local camera control with pattern '{0}'".format(camInfo['Namespace'] + CAM_LOCAL))

    if mc.objExists(camInfo['Namespace'] + CAM_DOLLY):
        camInfo['Dolly'] = pc.PyNode(camInfo['Namespace'] + CAM_DOLLY)
    else:
        pc.error("Can't find dolly camera control with pattern '{0}'".format(camInfo['Namespace'] + CAM_DOLLY))

    return camInfo

#GLOBALS METHODS
def canDo(s_inCommand, s_inTask):
    cmd = COMMANDS.get(s_inCommand)
    if cmd != None:
        return s_inTask in cmd

    return None

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
        print '{} initialization done ! ({})'.format("base", sceneManager.context)

    cmdCallable(sceneManager)
    print '{} initialization done ! ({})'.format(s_inTask, sceneManager.context)

def importSceneStructure(sceneManager):
    #Import only if does not exists...
    if pc.objExists('shot'):
        return

    sEntityType = sceneManager.context['entity']['type']

    #Import scene structure
    template_path = sceneManager.context['damProject'].getPath('template', 'project')
    strucure_path = os.path.join(template_path, "{0}_layout_tree.ma".format(sEntityType.lower()))

    if os.path.isfile(strucure_path):
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
    sceneManager.updateScene()

    init_scene_base(sceneManager)
    init_previz_scene(sceneManager)

    reArrangeAssets()

    #lock previz, save v001 in private, here ?
    privFile = sceneManager.edit(onBase=True)

    if privFile != None:
        #save the created file on the private
        pc.saveAs(privFile.absPath())

        print 'previz creation done ! ({0})'.format(sceneManager)
    else:
        print 'previz creation failed to Edit and save !'

#Inits
def init_shot_constants(sceneManager):
    start = 101

    duration = sceneManager.getDuration()

    pc.playbackOptions(edit=True, minTime=start)
    pc.playbackOptions(edit=True, animationStartTime=start)
    pc.playbackOptions(edit=True, maxTime=start + duration - 1)
    pc.playbackOptions(edit=True, animationEndTime=start + duration - 1)

def init_scene_base(sceneManager):
    #Set units
    angle = 'degree'
    linear = 'centimeter'
    time = 'film'
    pc.currentUnit(angle=angle, linear=linear, time=time)

    #color management
    pc.colorManagementPrefs(edit=True, cmEnabled=False)

    #Subdiv
    setSubdivPref(0)

    #Swatches size
    mc.optionVar(iv=('maxImageSizeForSwatchGen', 1000))

    #Legacy Viewport textures
    mc.displayPref(maxTextureResolution=1024)

    #Viewport 2.0 textures
    mc.setAttr("hardwareRenderingGlobals.enableTextureMaxRes", 1)
    mc.setAttr("hardwareRenderingGlobals.textureMaxResolution", 1024)

    #entity specific initialisation
    if sceneManager.context['entity']['type'] == 'Shot':
        init_shot_constants(sceneManager)

    importSceneStructure(sceneManager)

def arrangeViews(oShotCam, oImgPlaneCam=None):

    # Set Viewport
    pc.mel.eval('setNamedPanelLayout("Four View")')
    pc.mel.eval('ThreeRightSplitViewArrangement')

    #Image plane
    sidePanel = ""
    if oImgPlaneCam:
        sidePanel = mc.getPanel(withLabel='Side View')
        pc.modelPanel(sidePanel, edit=True, camera=oImgPlaneCam)
    #Camera
    perspPanel = mc.getPanel(withLabel='Persp View')
    pc.modelPanel(perspPanel, edit=True, camera=oShotCam)
    #Work view
    workPanel = mc.getPanel(withLabel='Top View')
    pc.modelPanel(workPanel, edit=True, camera='persp')

    if sidePanel:
        pc.modelEditor(sidePanel, edit=True, allObjects=0, imagePlane=True, grid=False)

    pc.setFocus(perspPanel)

def init_previz_scene(sceneManager):

    # --- Set Viewport 2.0 AO default Value
    pc.setAttr('hardwareRenderingGlobals.ssaoAmount', 0.3)
    pc.setAttr('hardwareRenderingGlobals.ssaoRadius', 8)
    pc.setAttr('hardwareRenderingGlobals.ssaoFilterRadius', 8)
    pc.setAttr('hardwareRenderingGlobals.ssaoSamples', 16)

    sTaskName = sceneManager.context["task"]["content"]
    sShotCamNspace = sceneManager.mkShotCamNamespace()
    proj = sceneManager.context["damProject"]
    shotLib = proj.getLibrary("public", "shot_lib")

    #rename any other shot camera
    remainingCamera = None

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
                    mc.setAttr(sCamNs + ":asset.visibility", False)
                    camsLength -= 1
        else:
            remainingCamera = otherCams[0]

        if remainingCamera and remainingCamera.parentNamespace() != sShotCamNspace:
            #rename camera
            pc.namespace(rename=(remainingCamera.namespace(), sShotCamNspace))

    oShotCam = sceneManager.getShotCamera()
    if not oShotCam:
        oShotCam = sceneManager.importShotCam()

    if sTaskName.lower() != "previz 3d":

        if not oShotCam.isReferenced():
            oShotCam = switchShotCamToRef(sceneManager, oShotCam)

        if (not sceneManager.isShotCamEdited()) and sceneManager.camAnimFilesExist():
            sceneManager.importShotCamAbcFile()

    sgEntity = sceneManager.context['entity']
    #image plane "Y:\shot\...\00_data\sqXXXX_shXXXXa_animatic.mov"
    imgPlanePath = sceneManager.getPath(sgEntity, 'animatic_capture')
    imgPlaneEnvPath = shotLib.absToEnvPath(imgPlanePath)
    IMGP = getImagePlaneItems(create=True)

    arrangeViews(oShotCam.getShape(), IMGP[1])

    if os.path.isfile(imgPlanePath):
        pc.currentTime(101)
        pc.refresh()
        pc.imagePlane(IMGP[0], edit=True, fileName=imgPlaneEnvPath)
    else:
        pc.warning('Image plane file cannot be found ({0})'.format(imgPlanePath))
        pc.setAttr(IMGP[0] + ".imageName", imgPlaneEnvPath, type="string")
        #pc.imagePlane(IMGP[0], edit=True, fileName="")

    #son "Y:\shot\...\00_data\sqXXXX_shXXXXa_sound.wav"
    soundPath = sceneManager.getPath(sgEntity, 'animatic_sound')
    pc.mel.DeleteAllSounds()
    if os.path.isfile(soundPath):
        # --- Import Sound
        # - Import current shot Sound
        soundEnvPath = shotLib.absToEnvPath(soundPath)
        audio_shot = pc.sound(offset=101, file=soundEnvPath, name='audio')

        # - Show Sound in Timeline
        aPlayBackSliderPython = pc.mel.eval('$tmpVar=$gPlayBackSlider')
        pc.timeControl(aPlayBackSliderPython, e=True, sound=audio_shot, displaySound=True)

    else:
        pc.warning('Sound file cannot be found ({0})'.format(soundPath))

    reArrangeAssets()

COMMANDS = {
    'create':{
        'BASE':create_scene_base,
        'previz 3D':create_previz_scene,
    },
    'init':{
        'BASE':init_scene_base,
        'previz 3D':init_previz_scene,
        'layout':init_previz_scene,
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

    bImgPlnViz = isImgPlaneVisible()
    setImgPlaneVisible(False)
    try:
        res = mc.AbcExport(j=sAbcJobArgs.replace("\n", " "))
    finally:
        setImgPlaneVisible(bImgPlnViz)

    print sHeader

    return res

def switchShotCamToRef(scnMng, oShotCam):

    if oShotCam.isReferenced():
        raise RuntimeError("{} is already a reference.".format(oShotCam))

    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(suffix=".atom", delete=False) as f:
        sAtomFilePath = os.path.normpath(f.name).replace("\\", "/")

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

REFNODE_ATTR = "defaultAssetFile"

def setDefaultAssetFileForSelectedRefs(assetFile="NoInput", **kwargs):

    damEntity = entityFromScene()
    proj = damEntity.project

    kwargs.update(confirm=False, allIfNoSelection=False, topReference=True)
    oSelRefList, assetRcList = listMayaRcForSelectedRefs(proj,
                                                         filter="previz_ref",
                                                         **kwargs)

    assetList = tuple(ast for ast, _ in assetRcList if ast)
    if not assetList:
        #pc.displayWarning("No Asset References selected !")
        return

    sRcNameSet = set()
    for _, rcDct in assetRcList:
        sRcNameSet.update(rcDct.iterkeys())

    if not sRcNameSet:
        pc.displayWarning("No available resources on which to switch !")

    sAstRcName = None

    sortedRcNames = sorted(sRcNameSet)
    allowedValues = sortedRcNames + ["offloaded", ""]
    if assetFile != "NoInput":
        if assetFile not in allowedValues:
            raise ValueError("Bad value for 'assetFile' kwarg: '{}'. Are valid: {}"
                             .format(assetFile, allowedValues))
        sAstRcName = assetFile
        sChoiceList = ["OK"]
    else:
        sChoiceList = sortedRcNames + ["offloaded", "Clear"]

    numRefs = len(oSelRefList)
    if sAstRcName is None:
        sMsg = "Set default asset file for {} references to...".format(numRefs)
    else:
        sMsg = ("Set default asset file for {} references to '{}'"
                .format(numRefs, sAstRcName))

    sChoice = pc.confirmDialog(title="Hey, mon ami !",
                               message=sMsg,
                               button=sChoiceList + ["Cancel"],
                               defaultButton='Cancel',
                               cancelButton='Cancel',
                               dismissString='Cancel',
                               icon="question")

    if sChoice == "Cancel":
        pc.displayWarning("Canceled !")
        return
    elif sChoice == "Clear":
        sAstRcName = ""
    elif sAstRcName is None:
        sAstRcName = sChoice

    for oFileRef in oSelRefList:

        oRefNode = oFileRef.refNode

        bHasAttr = oRefNode.hasAttr(REFNODE_ATTR)
        bAddAttr = True if sAstRcName and (not bHasAttr) else False

        if bAddAttr:
            pc.lockNode(oRefNode, lock=False)
            try:
                oRefNode.addAttr(REFNODE_ATTR, dt="string", k=False, r=True, w=True, s=True)
                bHasAttr = True
            finally:
                pc.lockNode(oRefNode, lock=True)

        if bHasAttr:
            print "set {}.{} to '{}'".format(oRefNode, REFNODE_ATTR, sAstRcName)
            oRefNode.setAttr(REFNODE_ATTR, sAstRcName)

def selectRefsWithDefaultAssetFile(assetFile="NoInput"):

    oRefNodeDct = {}
    for oFileRef in listReferences(loaded=True):
        oRefNode = oFileRef.refNode

        if not oRefNode.hasAttr(REFNODE_ATTR):
            continue

        sValue = oRefNode.getAttr(REFNODE_ATTR)
        if not sValue:
            continue

        oRefNodeDct.setdefault(sValue, []).append(oRefNode)

    sFoundValues = sorted(oRefNodeDct.iterkeys())

    if not sFoundValues:
        pc.displayWarning("No asset references to select !")

    if assetFile != "NoInput":
        if assetFile not in sFoundValues:
            pc.displayWarning("No refs with default asset file set to '{}'. Found {}."
                              .format(assetFile, sFoundValues))
            return
        sAstRcName = assetFile
    else:
        sChoice = pc.confirmDialog(title="Hey, mon ami !",
                                   message="",
                                   button=sFoundValues + ["Cancel"],
                                   defaultButton='Cancel',
                                   cancelButton='Cancel',
                                   dismissString='Cancel',
                                   icon="question")

        if sChoice == "Cancel":
            pc.displayWarning("Canceled !")
            return
        else:
            sAstRcName = sChoice

    sSelList = []
    count = 0
    for oRefNode in oRefNodeDct[sAstRcName]:

        sRefNode = oRefNode.name()
        sNodeList = mc.referenceQuery(sRefNode, nodes=True, dagPath=True)
        if sNodeList:
            sDagNodeList = mc.ls(sNodeList, type="dagNode")
            if sDagNodeList:
                sNodeList = sDagNodeList
            sNodeList = [sNodeList[0], sRefNode]
        else:
            sNodeList = [sRefNode]

        sSelList.extend(sNodeList)
        count += 1

    if sSelList:
        mc.select(sSelList, replace=True, noExpand=True)
        pc.displayInfo("{} references selected.".format(count))
    else:
        pc.displayWarning("No references to select !")

    return sSelList


from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

class SelectRefDialog(MayaQWidgetDockableMixin, QtGui.QDialog):

    def __init__(self, *args, **kwargs):
        super(SelectRefDialog, self).__init__(*args, **kwargs)

        self.setObjectName("SelectRefDialog")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowTitle("Select Refs With Default Asset File")

        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)

        buttonBox = QtGui.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Horizontal)
        buttonBox.setObjectName("buttonBox")

        btn = buttonBox.addButton("Close", QtGui.QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.accept)
        btn = buttonBox.addButton("Refresh", QtGui.QDialogButtonBox.ResetRole)
        btn.clicked.connect(self.refresh)

        layout.addWidget(buttonBox)

        self.refNodes = {}

        self.selectionButtons = self.createButtons()

    def createButtons(self):

        oRefNodeDct = {}
        for oFileRef in listReferences(loaded=True):
            oRefNode = oFileRef.refNode

            if not oRefNode.hasAttr(REFNODE_ATTR):
                continue

            sValue = oRefNode.getAttr(REFNODE_ATTR)
            if not sValue:
                continue

            oRefNodeDct.setdefault(sValue, []).append(oRefNode)

        sFoundValues = sorted(oRefNodeDct.iterkeys())

        buttonList = []
        layout = self.layout()

        if not sFoundValues:
#            btn = QtGui.QPushButton("No ref with default asset file.", self)
#            layout.insertWidget(0, btn)
#            buttonList.append(btn)
            return buttonList

        self.refNodes = oRefNodeDct

        for sValue in sFoundValues:
            btn = QtGui.QPushButton(sValue, self)
            buttonList.append(btn)

            layout.insertWidget(0, btn)
            slot = partial(self.selectReferences, sValue)
            btn.clicked.connect(slot)

        return buttonList

    def selectReferences(self, sAstRcName):

        oRefNodeDct = self.refNodes

        sSelList = []
        count = 0
        for oRefNode in oRefNodeDct[sAstRcName]:

            sRefNode = oRefNode.name()
            sNodeList = mc.referenceQuery(sRefNode, nodes=True, dagPath=True)
            if sNodeList:
                sDagNodeList = mc.ls(sNodeList, type="dagNode")
                if sDagNodeList:
                    sNodeList = sDagNodeList
                sNodeList = [sNodeList[0], sRefNode]
            else:
                sNodeList = [sRefNode]

            sSelList.extend(sNodeList)
            count += 1

        if sSelList:
            mc.select(sSelList, replace=True, noExpand=True)
            pc.displayInfo("{} references selected.".format(count))
        else:
            pc.displayWarning("No references to select !")

    def refresh(self):

        layout = self.layout()
        for btn in self.selectionButtons:
            btn.close()
            layout.removeWidget(btn)
            btn.deleteLater()

        self.selectionButtons = self.createButtons()
