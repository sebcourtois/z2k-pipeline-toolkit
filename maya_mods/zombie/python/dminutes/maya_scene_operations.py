
import os
import re
#from itertools import izip

import pymel.core as pc
import maya.cmds as mc

from pytd.util.sysutils import toStr
from davos_maya.tool.reference import loadReferencesForAnim, listPrevizRefMeshes
from dminutes.shotconformation import removeRefEditByAttr
from pytaya.util.sysutils import withSelectionRestored
from collections import OrderedDict
from pytaya.core.transform import matchTransform
from pytd.util.fsutils import jsonWrite


CAMPATTERN = 'cam_sq????_sh?????:*'
CAM_GLOBAL = 'Global_SRT'
CAM_LOCAL = 'Local_SRT'
CAM_DOLLY = 'Dolly'

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
string $cmd = `format -s $frame -s $sep -s $conv "mop.recStereoInfos(^1s, separation=^2s, convergence=^3s)"`;
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

    sDirPath = os.path.dirname(sFilePath)
    if not os.path.exists(sDirPath):
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

    oImgPlaneList = pc.ls("cam_animatic:assetShape->imgPlane_animatic")
    if oImgPlaneList:
        oImgPlane = oImgPlaneList[0]

    if (not oImgPlane):
        if not create:
            return None, None
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
            #mc.parent( CAM_Animatic[0], grpDict['GD_ROOT'] )

            _, oImgPlane = pc.imagePlane(camera=oCamShape,
                                         showInAllViews=False,
                                         name="imgPlane_animatic")
            oImgPlane.rename("imgPlane_animatic")

            #SET DE L'IMAGE PLANE
            sImgPlane = oImgPlane.name()
            pc.setAttr(sImgPlane + ".type", 2)
            pc.setAttr(sImgPlane + ".fit", 1)
            pc.setAttr(sImgPlane + ".useFrameExtension", 1)
            pc.setAttr(sImgPlane + ".frameOffset", -100)
            pc.setAttr(sImgPlane + ".frameIn", 101)
            pc.setAttr(sImgPlane + ".frameOut", 1000)
            #pc.setAttr(sImgPlane + ".hideOnPlayback", False)

            sCamShape = oCamShape.name()
            pc.setAttr(sCamShape + ".displayFilmGate", 1)
            pc.setAttr(sCamShape + ".displayGateMask", 1)
            pc.setAttr(sCamShape + ".overscan", 1.4)
            pc.setAttr(sCamShape + ".displaySafeTitle", 1)
            pc.setAttr(sCamShape + ".displaySafeAction", 1)
            pc.setAttr(sCamShape + ".displayGateMaskColor", [0, 0, 0])
    else:
        oCamXfm = oImgPlane.getParent(3)
        oCamShape = oCamXfm.getShape()

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
        'fxp':'grp_fx',
        'cwp':'grp_crowd',
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

def setMayaProject(sProjName):

    sMayaProjsLoc = os.path.dirname(os.path.normpath(mc.workspace(q=True, rd=True)))
    sMyaProjPath = os.path.join(sMayaProjsLoc, sProjName)

    if not os.path.exists(sMyaProjPath):
        os.mkdir(sMyaProjPath)

    mc.workspace(sProjName, openWorkspace=True)
    if not mc.workspace(fileRuleEntry="movie"):
        mc.workspace(fileRule=("movie", "captures"))
        mc.workspace(saveWorkspace=True)

    return sMyaProjPath

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

def arrangeViews(oShotCam, oImgPlaneCam=None, oStereoCam=None,
                 singleView=False, stereoDisplay="anaglyph"):

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

@withSelectionRestored
def addNode(sNodeType, sNodeName, unique=True):
    if unique and mc.objExists(sNodeName):
        return sNodeName
    return mc.createNode(sNodeType, name=sNodeName)

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

    from pytaya.util import apiutils as mapi

    maxFaxes = pc.optionVar["smpSizeOfMeshForWarning"]
    nonSmoothableList = []


    sAllMeshSet = set(listMeshesToSmooth())
    numMeshes = len(sAllMeshSet)
    numFailure = 0

    sPrevizMeshSet = set(listPrevizRefMeshes(project=project))
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

        dagPath = mapi.getDagPath(sMesh)
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

@withSelectionRestored
def init_previz_scene(sceneManager):

    # --- Set Viewport 2.0 AO default Value
    pc.setAttr('hardwareRenderingGlobals.ssaoAmount', 0.3)
    pc.setAttr('hardwareRenderingGlobals.ssaoRadius', 8)
    pc.setAttr('hardwareRenderingGlobals.ssaoFilterRadius', 8)
    pc.setAttr('hardwareRenderingGlobals.ssaoSamples', 16)

    sStepName = sceneManager.context["step"]["code"].lower()
    proj = sceneManager.context["damProject"]
    shotLib = proj.getLibrary("public", "shot_lib")
    sShotCode = sceneManager.context['entity']['code']

    if sStepName == "animation":
        if not pc.listReferences(loaded=True, unloaded=False):
            removeRefEditByAttr(attr=("smoothDrawType",
                                      "displaySmoothMesh",
                                      "dispResolution"),
                                GUI=False)
            loadReferencesForAnim(project=proj)

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

        if not oShotCam.isReferenced():
            switchShotCamToRef(sceneManager, oShotCam)

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

    sgEntity = sceneManager.context['entity']
    #image plane "Y:\shot\...\00_data\sqXXXX_shXXXXa_animatic.mov"
    imgPlanePath = sceneManager.getPath(sgEntity, 'animatic_capture')
    imgPlaneEnvPath = shotLib.absToEnvPath(imgPlanePath)
    oImagePlane, oImagePlaneCam = getImagePlaneItems(create=True)

    arrangeViews(oShotCam.getShape(), oImagePlaneCam, oStereoCam)

    if os.path.isfile(imgPlanePath):
        pc.currentTime(101)
        pc.refresh()
        pc.imagePlane(oImagePlane, edit=True, fileName=imgPlaneEnvPath)
    else:
        pc.warning('Image plane file cannot be found ({0})'.format(imgPlanePath))
        oImagePlane.setAttr("imageName", imgPlaneEnvPath, type="string")
        #pc.imagePlane(oImagePlane, edit=True, fileName="")

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
        'stereo':init_previz_scene,
        'layout':init_previz_scene,
        'animation':init_previz_scene,
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
